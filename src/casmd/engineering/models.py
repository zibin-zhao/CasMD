"""Data contract for trajectory-guided mutation and truncation design."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class RegionObjective(str, Enum):
    WEAKEN = "weaken"
    PRESERVE = "preserve"
    MONITOR = "monitor"


@dataclass(frozen=True, order=True)
class ResidueKey:
    segid: str
    resid: int
    resname: str

    def __post_init__(self) -> None:
        if not self.resname.strip():
            raise ValueError("resname must not be empty")

    @property
    def token(self) -> str:
        return f"{self.segid or '_'}:{self.resid}"

    def to_dict(self) -> dict[str, Any]:
        return {"segid": self.segid, "resid": self.resid, "resname": self.resname}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ResidueKey":
        return cls(str(value.get("segid", "")), int(value["resid"]), str(value["resname"]))


@dataclass(frozen=True)
class RegionSpec:
    region_id: str
    label: str
    selection: str
    objective: RegionObjective
    cutoff_A: float = 4.0

    def __post_init__(self) -> None:
        if not self.region_id.strip() or not self.label.strip() or not self.selection.strip():
            raise ValueError("region_id, label, and selection must not be empty")
        if self.cutoff_A <= 0:
            raise ValueError("cutoff_A must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "label": self.label,
            "selection": self.selection,
            "objective": self.objective.value,
            "cutoff_A": self.cutoff_A,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RegionSpec":
        return cls(
            region_id=str(value["region_id"]),
            label=str(value["label"]),
            selection=str(value["selection"]),
            objective=RegionObjective(value["objective"]),
            cutoff_A=float(value.get("cutoff_A", 4.0)),
        )


@dataclass(frozen=True)
class TruncationSpec:
    truncation_id: str
    segid: str
    start_resid: int
    end_resid: int

    def __post_init__(self) -> None:
        if not self.truncation_id.strip():
            raise ValueError("truncation_id must not be empty")
        if self.start_resid > self.end_resid:
            raise ValueError("start_resid must be <= end_resid")

    def contains(self, residue: ResidueKey) -> bool:
        segid_matches = not self.segid or self.segid == "*" or residue.segid == self.segid
        return segid_matches and self.start_resid <= residue.resid <= self.end_resid

    def to_dict(self) -> dict[str, Any]:
        return {
            "truncation_id": self.truncation_id,
            "segid": self.segid,
            "start_resid": self.start_resid,
            "end_resid": self.end_resid,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TruncationSpec":
        return cls(
            truncation_id=str(value["truncation_id"]),
            segid=str(value.get("segid", "")),
            start_resid=int(value["start_resid"]),
            end_resid=int(value["end_resid"]),
        )


@dataclass(frozen=True)
class EngineeringConfig:
    protein_selection: str
    regions: tuple[RegionSpec, ...]
    protected_residues: tuple[str, ...] = field(default_factory=tuple)
    mutation_budget: int = 5
    min_occupancy: float = 0.05
    preservation_weight: float = 1.0
    risk_weight: float = 1.0
    o2prime_bonus: float = 0.25
    max_preservation_burden: float = 0.40
    max_cumulative_risk: float = 1.50
    coverage_weight: float = 0.75
    truncation_coverage_gate: float = 0.50
    risk_by_residue: Mapping[str, float] = field(default_factory=dict)
    truncations: tuple[TruncationSpec, ...] = field(default_factory=tuple)
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.protein_selection.strip():
            raise ValueError("protein_selection must not be empty")
        if not self.regions:
            raise ValueError("at least one region is required")
        region_ids = [item.region_id for item in self.regions]
        if len(region_ids) != len(set(region_ids)):
            raise ValueError("region_id values must be unique")
        if not any(item.objective == RegionObjective.WEAKEN for item in self.regions):
            raise ValueError("at least one weaken region is required")
        if self.mutation_budget < 1:
            raise ValueError("mutation_budget must be >= 1")
        for label, value in (
            ("min_occupancy", self.min_occupancy),
            ("max_preservation_burden", self.max_preservation_burden),
            ("truncation_coverage_gate", self.truncation_coverage_gate),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{label} must be between 0 and 1")
        if any(float(value) < 0 for value in self.risk_by_residue.values()):
            raise ValueError("risk values must be non-negative")

    def is_protected(self, residue: ResidueKey) -> bool:
        return residue.token in self.protected_residues or f"*:{residue.resid}" in self.protected_residues

    def risk_for(self, residue: ResidueKey) -> float:
        return float(
            self.risk_by_residue.get(
                residue.token, self.risk_by_residue.get(f"*:{residue.resid}", 0.0)
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "protein_selection": self.protein_selection,
            "regions": [item.to_dict() for item in self.regions],
            "protected_residues": list(self.protected_residues),
            "mutation_budget": self.mutation_budget,
            "min_occupancy": self.min_occupancy,
            "preservation_weight": self.preservation_weight,
            "risk_weight": self.risk_weight,
            "o2prime_bonus": self.o2prime_bonus,
            "max_preservation_burden": self.max_preservation_burden,
            "max_cumulative_risk": self.max_cumulative_risk,
            "coverage_weight": self.coverage_weight,
            "truncation_coverage_gate": self.truncation_coverage_gate,
            "risk_by_residue": dict(self.risk_by_residue),
            "truncations": [item.to_dict() for item in self.truncations],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EngineeringConfig":
        return cls(
            protein_selection=str(value["protein_selection"]),
            regions=tuple(RegionSpec.from_dict(item) for item in value["regions"]),
            protected_residues=tuple(str(item) for item in value.get("protected_residues", [])),
            mutation_budget=int(value.get("mutation_budget", 5)),
            min_occupancy=float(value.get("min_occupancy", 0.05)),
            preservation_weight=float(value.get("preservation_weight", 1.0)),
            risk_weight=float(value.get("risk_weight", 1.0)),
            o2prime_bonus=float(value.get("o2prime_bonus", 0.25)),
            max_preservation_burden=float(value.get("max_preservation_burden", 0.40)),
            max_cumulative_risk=float(value.get("max_cumulative_risk", 1.50)),
            coverage_weight=float(value.get("coverage_weight", 0.75)),
            truncation_coverage_gate=float(value.get("truncation_coverage_gate", 0.50)),
            risk_by_residue={
                str(key): float(risk) for key, risk in value.get("risk_by_residue", {}).items()
            },
            truncations=tuple(
                TruncationSpec.from_dict(item) for item in value.get("truncations", [])
            ),
            schema_version=int(value.get("schema_version", 1)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, allow_nan=False)


@dataclass(frozen=True)
class ContactObservation:
    frame_index: int
    protein: ResidueKey
    region_id: str
    nucleotide: ResidueKey
    min_distance_A: float
    o2prime_contact: bool = False


@dataclass(frozen=True)
class NucleotideContact:
    nucleotide: ResidueKey
    occupancy: float

    def to_dict(self) -> dict[str, Any]:
        return {"nucleotide": self.nucleotide.to_dict(), "occupancy": self.occupancy}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "NucleotideContact":
        return cls(ResidueKey.from_dict(value["nucleotide"]), float(value["occupancy"]))


@dataclass(frozen=True)
class RegionFingerprint:
    protein: ResidueKey
    region_id: str
    contact_occupancy: float
    mean_contact_distance_A: float
    p10_contact_distance_A: float
    contact_events: int
    longest_run_frames: int
    o2prime_occupancy: float
    nucleotide_contacts: tuple[NucleotideContact, ...] = field(default_factory=tuple)

    @property
    def nucleotide_coverage(self) -> int:
        return len(self.nucleotide_contacts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "protein": self.protein.to_dict(),
            "region_id": self.region_id,
            "contact_occupancy": self.contact_occupancy,
            "mean_contact_distance_A": self.mean_contact_distance_A,
            "p10_contact_distance_A": self.p10_contact_distance_A,
            "contact_events": self.contact_events,
            "longest_run_frames": self.longest_run_frames,
            "o2prime_occupancy": self.o2prime_occupancy,
            "nucleotide_contacts": [item.to_dict() for item in self.nucleotide_contacts],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RegionFingerprint":
        return cls(
            protein=ResidueKey.from_dict(value["protein"]),
            region_id=str(value["region_id"]),
            contact_occupancy=float(value["contact_occupancy"]),
            mean_contact_distance_A=float(value["mean_contact_distance_A"]),
            p10_contact_distance_A=float(value["p10_contact_distance_A"]),
            contact_events=int(value["contact_events"]),
            longest_run_frames=int(value["longest_run_frames"]),
            o2prime_occupancy=float(value.get("o2prime_occupancy", 0.0)),
            nucleotide_contacts=tuple(
                NucleotideContact.from_dict(item) for item in value.get("nucleotide_contacts", [])
            ),
        )


@dataclass(frozen=True)
class MutationCandidate:
    protein: ResidueKey
    suggested_mutation: str
    target_engagement: float
    preservation_burden: float
    structural_risk: float
    o2prime_signal: float
    design_score: float
    target_pairs: tuple[str, ...]
    eligible: bool
    exclusion_reason: str = ""
    rationale: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "protein": self.protein.to_dict(),
            "suggested_mutation": self.suggested_mutation,
            "target_engagement": self.target_engagement,
            "preservation_burden": self.preservation_burden,
            "structural_risk": self.structural_risk,
            "o2prime_signal": self.o2prime_signal,
            "design_score": self.design_score,
            "target_pairs": list(self.target_pairs),
            "eligible": self.eligible,
            "exclusion_reason": self.exclusion_reason,
            "rationale": list(self.rationale),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MutationCandidate":
        return cls(
            protein=ResidueKey.from_dict(value["protein"]),
            suggested_mutation=str(value["suggested_mutation"]),
            target_engagement=float(value["target_engagement"]),
            preservation_burden=float(value["preservation_burden"]),
            structural_risk=float(value["structural_risk"]),
            o2prime_signal=float(value.get("o2prime_signal", 0.0)),
            design_score=float(value["design_score"]),
            target_pairs=tuple(str(item) for item in value.get("target_pairs", [])),
            eligible=bool(value["eligible"]),
            exclusion_reason=str(value.get("exclusion_reason", "")),
            rationale=tuple(str(item) for item in value.get("rationale", [])),
        )


@dataclass(frozen=True)
class MutationSet:
    selected: tuple[MutationCandidate, ...]
    target_pair_coverage: float
    preservation_burden: float
    cumulative_risk: float
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected": [item.to_dict() for item in self.selected],
            "target_pair_coverage": self.target_pair_coverage,
            "preservation_burden": self.preservation_burden,
            "cumulative_risk": self.cumulative_risk,
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MutationSet":
        return cls(
            selected=tuple(MutationCandidate.from_dict(item) for item in value["selected"]),
            target_pair_coverage=float(value["target_pair_coverage"]),
            preservation_burden=float(value["preservation_burden"]),
            cumulative_risk=float(value["cumulative_risk"]),
            warnings=tuple(str(item) for item in value.get("warnings", [])),
        )


@dataclass(frozen=True)
class TruncationAudit:
    truncation: TruncationSpec
    target_coverage_removed: float
    preserve_coverage_removed: float
    unwanted_interaction_remaining: float
    distributed_interface_warning: bool
    remaining_candidate_residues: tuple[str, ...]
    flexibility_ratio: float | None
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "truncation": self.truncation.to_dict(),
            "target_coverage_removed": self.target_coverage_removed,
            "preserve_coverage_removed": self.preserve_coverage_removed,
            "unwanted_interaction_remaining": self.unwanted_interaction_remaining,
            "distributed_interface_warning": self.distributed_interface_warning,
            "remaining_candidate_residues": list(self.remaining_candidate_residues),
            "flexibility_ratio": self.flexibility_ratio,
            "interpretation": self.interpretation,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TruncationAudit":
        ratio = value.get("flexibility_ratio")
        return cls(
            truncation=TruncationSpec.from_dict(value["truncation"]),
            target_coverage_removed=float(value["target_coverage_removed"]),
            preserve_coverage_removed=float(value["preserve_coverage_removed"]),
            unwanted_interaction_remaining=float(value["unwanted_interaction_remaining"]),
            distributed_interface_warning=bool(value["distributed_interface_warning"]),
            remaining_candidate_residues=tuple(
                str(item) for item in value.get("remaining_candidate_residues", [])
            ),
            flexibility_ratio=None if ratio is None else float(ratio),
            interpretation=str(value["interpretation"]),
        )


@dataclass(frozen=True)
class RegionComparison:
    region_id: str
    objective: RegionObjective
    baseline_mass: float
    variant_mass: float
    retention_pct: float | None
    objective_change: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "objective": self.objective.value,
            "baseline_mass": self.baseline_mass,
            "variant_mass": self.variant_mass,
            "retention_pct": self.retention_pct,
            "objective_change": self.objective_change,
        }


@dataclass(frozen=True)
class VariantComparison:
    baseline_label: str
    variant_label: str
    regions: tuple[RegionComparison, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_label": self.baseline_label,
            "variant_label": self.variant_label,
            "regions": [item.to_dict() for item in self.regions],
        }


@dataclass(frozen=True)
class DesignReport:
    config: EngineeringConfig
    n_frames: int
    frame_interval_ps: float | None
    source_label: str
    fingerprints: tuple[RegionFingerprint, ...]
    candidates: tuple[MutationCandidate, ...]
    mutation_set: MutationSet
    truncation_audits: tuple[TruncationAudit, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "config": self.config.to_dict(),
            "n_frames": self.n_frames,
            "frame_interval_ps": self.frame_interval_ps,
            "source_label": self.source_label,
            "fingerprints": [item.to_dict() for item in self.fingerprints],
            "candidates": [item.to_dict() for item in self.candidates],
            "mutation_set": self.mutation_set.to_dict(),
            "truncation_audits": [item.to_dict() for item in self.truncation_audits],
            "provenance": dict(self.provenance),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, allow_nan=False)

