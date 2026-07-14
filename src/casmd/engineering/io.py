"""Build, load, and validate portable guided-engineering reports."""
from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from casmd.engineering.design import (
    audit_truncation,
    rank_mutation_candidates,
    select_mutation_set,
)
from casmd.engineering.fingerprint import aggregate_contacts
from casmd.engineering.models import (
    ContactObservation,
    DesignReport,
    EngineeringConfig,
    MutationCandidate,
    MutationSet,
    RegionFingerprint,
    TruncationAudit,
)


def build_design_report(
    *,
    config: EngineeringConfig,
    n_frames: int,
    source_label: str,
    observations: Iterable[ContactObservation] | None = None,
    fingerprints: Iterable[RegionFingerprint] | None = None,
    frame_interval_ps: float | None = None,
    provenance: Mapping[str, Any] | None = None,
    rmsf_by_residue: Mapping[str, float] | None = None,
) -> DesignReport:
    """Build a complete design report from contacts or precomputed fingerprints."""
    if observations is None and fingerprints is None:
        raise ValueError("observations or fingerprints must be provided")
    if observations is not None and fingerprints is not None:
        raise ValueError("provide observations or fingerprints, not both")
    if fingerprints is None:
        computed = aggregate_contacts(observations or (), n_frames=n_frames)
    else:
        computed = tuple(fingerprints)
    candidates = rank_mutation_candidates(config, computed)
    mutation_set = select_mutation_set(config, candidates)
    audits = tuple(
        audit_truncation(
            config, computed, truncation, rmsf_by_residue=rmsf_by_residue
        )
        for truncation in config.truncations
    )
    return DesignReport(
        config=config,
        n_frames=n_frames,
        frame_interval_ps=frame_interval_ps,
        source_label=source_label,
        fingerprints=computed,
        candidates=candidates,
        mutation_set=mutation_set,
        truncation_audits=audits,
        provenance=dict(provenance or {}),
    )


def load_design_report(payload: str | bytes | Mapping[str, Any]) -> DesignReport:
    """Load either a complete report or raw trajectory fingerprint payload."""
    if isinstance(payload, bytes):
        data = json.loads(payload.decode("utf-8"))
    elif isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = dict(payload)
    config = EngineeringConfig.from_dict(data["config"])
    fingerprints = tuple(
        RegionFingerprint.from_dict(item) for item in data.get("fingerprints", [])
    )
    if "candidates" not in data or "mutation_set" not in data:
        return build_design_report(
            config=config,
            n_frames=int(data["n_frames"]),
            frame_interval_ps=(
                None if data.get("frame_interval_ps") is None
                else float(data["frame_interval_ps"])
            ),
            source_label=str(data.get("source_label", "trajectory")),
            fingerprints=fingerprints,
            provenance=data.get("provenance", {}),
            rmsf_by_residue=data.get("rmsf_by_residue"),
        )
    return DesignReport(
        config=config,
        n_frames=int(data["n_frames"]),
        frame_interval_ps=(
            None if data.get("frame_interval_ps") is None
            else float(data["frame_interval_ps"])
        ),
        source_label=str(data.get("source_label", "trajectory")),
        fingerprints=fingerprints,
        candidates=tuple(
            MutationCandidate.from_dict(item) for item in data.get("candidates", [])
        ),
        mutation_set=MutationSet.from_dict(data["mutation_set"]),
        truncation_audits=tuple(
            TruncationAudit.from_dict(item) for item in data.get("truncation_audits", [])
        ),
        provenance=data.get("provenance", {}),
    )

