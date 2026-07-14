"""Extract dynamic contact fingerprints from an MDAnalysis Universe."""
from __future__ import annotations

from typing import Any

from MDAnalysis.lib.distances import capped_distance

from casmd.engineering.fingerprint import ContactAccumulator
from casmd.engineering.models import (
    ContactObservation,
    EngineeringConfig,
    RegionFingerprint,
    ResidueKey,
)


def _residue_key(atom: Any) -> ResidueKey:
    return ResidueKey(str(atom.segid or ""), int(atom.resid), str(atom.resname))


def _is_o2prime(atom_name: str) -> bool:
    normalized = atom_name.upper().replace("*", "'")
    return normalized in {"O2'", "O2"}


def fingerprints_from_universe(
    universe: Any,
    config: EngineeringConfig,
    *,
    start: int = 0,
    stop: int | None = None,
    step: int = 1,
) -> tuple[tuple[RegionFingerprint, ...], int, float | None]:
    """Calculate contact fingerprints with capped-distance neighbor search."""
    if step < 1:
        raise ValueError("step must be >= 1")
    protein = universe.select_atoms(f"({config.protein_selection}) and not name H*")
    if len(protein) == 0:
        raise ValueError(f"protein selection matched no atoms: {config.protein_selection}")

    regions = []
    for region in config.regions:
        atoms = universe.select_atoms(f"({region.selection}) and not name H*")
        if len(atoms) == 0:
            raise ValueError(
                f"region {region.region_id!r} selection matched no atoms: {region.selection}"
            )
        regions.append((region, atoms))

    protein_keys = tuple(_residue_key(atom) for atom in protein)
    accumulator = ContactAccumulator()
    analysis_frame = 0
    for ts in universe.trajectory[start:stop:step]:
        frame_observations = []
        box = ts.dimensions if ts.dimensions is not None and ts.dimensions.size >= 3 else None
        for region, region_atoms in regions:
            pairs, distances = capped_distance(
                protein.positions,
                region_atoms.positions,
                max_cutoff=region.cutoff_A,
                box=box,
                return_distances=True,
            )
            for (protein_index, region_index), distance in zip(pairs, distances):
                region_atom = region_atoms[int(region_index)]
                frame_observations.append(
                    ContactObservation(
                        frame_index=analysis_frame,
                        protein=protein_keys[int(protein_index)],
                        region_id=region.region_id,
                        nucleotide=_residue_key(region_atom),
                        min_distance_A=float(distance),
                        o2prime_contact=_is_o2prime(str(region_atom.name)),
                    )
                )
        accumulator.add_frame(analysis_frame, frame_observations)
        analysis_frame += 1
    if analysis_frame == 0:
        raise ValueError("trajectory slice contains no frames")
    frame_interval_ps = None
    try:
        frame_interval_ps = float(universe.trajectory.dt) * step
    except (TypeError, ValueError, AttributeError):
        pass
    return accumulator.fingerprints(), analysis_frame, frame_interval_ps

