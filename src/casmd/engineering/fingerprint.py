"""Aggregate frame-level contacts into dynamic interaction fingerprints."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

from casmd.engineering.models import (
    ContactObservation,
    NucleotideContact,
    RegionFingerprint,
    ResidueKey,
)


def _events_and_longest_run(frames: list[int]) -> tuple[int, int]:
    if not frames:
        return 0, 0
    events = 1
    longest = 1
    current = 1
    for previous, current_frame in zip(frames, frames[1:]):
        if current_frame == previous + 1:
            current += 1
            longest = max(longest, current)
        else:
            events += 1
            current = 1
    return events, longest


def aggregate_contacts(
    observations: Iterable[ContactObservation], *, n_frames: int
) -> tuple[RegionFingerprint, ...]:
    """Deduplicate observations and calculate residue/region dynamics.

    One residue/nucleotide pair can have several atom pairs in a frame. The
    closest distance is retained and every occupancy is counted at most once
    per frame.
    """
    if n_frames <= 0:
        raise ValueError("n_frames must be positive")

    # (protein, region, nucleotide, frame) -> (minimum distance, any O2' contact)
    deduplicated: dict[tuple[ResidueKey, str, ResidueKey, int], tuple[float, bool]] = {}
    for observation in observations:
        if not 0 <= observation.frame_index < n_frames:
            raise ValueError(
                f"frame_index {observation.frame_index} outside 0..{n_frames - 1}"
            )
        if observation.min_distance_A < 0:
            raise ValueError("min_distance_A must be non-negative")
        key = (
            observation.protein,
            observation.region_id,
            observation.nucleotide,
            observation.frame_index,
        )
        existing = deduplicated.get(key)
        if existing is None:
            deduplicated[key] = (
                float(observation.min_distance_A), observation.o2prime_contact
            )
        else:
            deduplicated[key] = (
                min(existing[0], float(observation.min_distance_A)),
                existing[1] or observation.o2prime_contact,
            )

    by_residue_region: dict[tuple[ResidueKey, str], dict[int, list[tuple]]] = defaultdict(
        lambda: defaultdict(list)
    )
    pair_frames: dict[tuple[ResidueKey, str, ResidueKey], set[int]] = defaultdict(set)
    for (protein, region_id, nucleotide, frame), (distance, o2prime) in deduplicated.items():
        by_residue_region[(protein, region_id)][frame].append(
            (nucleotide, distance, o2prime)
        )
        pair_frames[(protein, region_id, nucleotide)].add(frame)

    fingerprints = []
    for (protein, region_id), frame_values in by_residue_region.items():
        frames = sorted(frame_values)
        minimum_distances = [
            min(item[1] for item in frame_values[frame]) for frame in frames
        ]
        o2prime_frames = sum(
            any(item[2] for item in frame_values[frame]) for frame in frames
        )
        events, longest = _events_and_longest_run(frames)
        nucleotide_contacts = tuple(
            sorted(
                (
                    NucleotideContact(nucleotide=nucleotide, occupancy=len(pair_frame_set) / n_frames)
                    for (pair_protein, pair_region, nucleotide), pair_frame_set in pair_frames.items()
                    if pair_protein == protein and pair_region == region_id
                ),
                key=lambda item: (item.nucleotide.segid, item.nucleotide.resid),
            )
        )
        fingerprints.append(
            RegionFingerprint(
                protein=protein,
                region_id=region_id,
                contact_occupancy=len(frames) / n_frames,
                mean_contact_distance_A=float(np.mean(minimum_distances)),
                p10_contact_distance_A=float(np.percentile(minimum_distances, 10)),
                contact_events=events,
                longest_run_frames=longest,
                o2prime_occupancy=o2prime_frames / n_frames,
                nucleotide_contacts=nucleotide_contacts,
            )
        )
    return tuple(
        sorted(
            fingerprints,
            key=lambda item: (item.protein.segid, item.protein.resid, item.region_id),
        )
    )


@dataclass
class _StreamingState:
    protein: ResidueKey
    region_id: str
    contact_frames: int = 0
    distances: list[float] = field(default_factory=list)
    o2prime_frames: int = 0
    contact_events: int = 0
    current_run: int = 0
    longest_run: int = 0
    last_frame: int | None = None
    nucleotide_counts: dict[ResidueKey, int] = field(default_factory=lambda: defaultdict(int))


class ContactAccumulator:
    """Streaming aggregator for large trajectories.

    Call `add_frame` once for every analyzed frame, including frames with no
    observations. Only per-residue distance samples and pair counts are kept.
    """

    def __init__(self) -> None:
        self._states: dict[tuple[ResidueKey, str], _StreamingState] = {}
        self._frames_seen: set[int] = set()

    def add_frame(
        self, frame_index: int, observations: Iterable[ContactObservation]
    ) -> None:
        if frame_index in self._frames_seen:
            raise ValueError(f"frame {frame_index} was added more than once")
        if frame_index < 0:
            raise ValueError("frame_index must be non-negative")
        self._frames_seen.add(frame_index)

        # Deduplicate atom-level observations within this frame.
        pairs: dict[tuple[ResidueKey, str, ResidueKey], tuple[float, bool]] = {}
        for observation in observations:
            if observation.frame_index != frame_index:
                raise ValueError("observation frame_index does not match add_frame")
            key = (observation.protein, observation.region_id, observation.nucleotide)
            previous = pairs.get(key)
            if previous is None:
                pairs[key] = (observation.min_distance_A, observation.o2prime_contact)
            else:
                pairs[key] = (
                    min(previous[0], observation.min_distance_A),
                    previous[1] or observation.o2prime_contact,
                )

        residue_regions: dict[tuple[ResidueKey, str], list[tuple]] = defaultdict(list)
        for (protein, region_id, nucleotide), (distance, o2prime) in pairs.items():
            residue_regions[(protein, region_id)].append((nucleotide, distance, o2prime))

        for (protein, region_id), values in residue_regions.items():
            key = (protein, region_id)
            state = self._states.setdefault(key, _StreamingState(protein, region_id))
            state.contact_frames += 1
            state.distances.append(min(item[1] for item in values))
            state.o2prime_frames += int(any(item[2] for item in values))
            if state.last_frame is None or frame_index != state.last_frame + 1:
                state.contact_events += 1
                state.current_run = 1
            else:
                state.current_run += 1
            state.longest_run = max(state.longest_run, state.current_run)
            state.last_frame = frame_index
            for nucleotide, _, _ in values:
                state.nucleotide_counts[nucleotide] += 1

    def fingerprints(self) -> tuple[RegionFingerprint, ...]:
        n_frames = len(self._frames_seen)
        if n_frames == 0:
            raise ValueError("no frames were added")
        output = []
        for state in self._states.values():
            nucleotide_contacts = tuple(
                NucleotideContact(nucleotide, count / n_frames)
                for nucleotide, count in sorted(
                    state.nucleotide_counts.items(),
                    key=lambda item: (item[0].segid, item[0].resid),
                )
            )
            output.append(
                RegionFingerprint(
                    protein=state.protein,
                    region_id=state.region_id,
                    contact_occupancy=state.contact_frames / n_frames,
                    mean_contact_distance_A=float(np.mean(state.distances)),
                    p10_contact_distance_A=float(np.percentile(state.distances, 10)),
                    contact_events=state.contact_events,
                    longest_run_frames=state.longest_run,
                    o2prime_occupancy=state.o2prime_frames / n_frames,
                    nucleotide_contacts=nucleotide_contacts,
                )
            )
        return tuple(
            sorted(
                output,
                key=lambda item: (
                    item.protein.segid,
                    item.protein.resid,
                    item.region_id,
                ),
            )
        )

