"""Project metadata for condition- and replicate-aware MD comparisons."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class SystemClass(str, Enum):
    PROTEIN_DNA = "protein_dna"
    PROTEIN_RNA = "protein_rna"
    PROTEIN_NUCLEIC_ACID_TERNARY = "protein_nucleic_acid_ternary"


class GuideMode(str, Enum):
    RNA = "crRNA"
    DNA = "crDNA"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class Replicate:
    """One independently initialized simulation run within a condition."""

    replicate_id: str
    seed: int | None = None
    trajectory_ns: float | None = None
    analysis_archive: str | None = None

    def __post_init__(self) -> None:
        if not self.replicate_id.strip():
            raise ValueError("replicate_id must not be empty")
        if self.trajectory_ns is not None and self.trajectory_ns <= 0:
            raise ValueError("trajectory_ns must be positive")


@dataclass(frozen=True)
class Condition:
    """A biological/design condition containing zero or more replicates."""

    condition_id: str
    label: str
    variant: str
    guide_mode: GuideMode = GuideMode.NOT_APPLICABLE
    replicates: tuple[Replicate, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.condition_id.strip() or not self.label.strip():
            raise ValueError("condition_id and label must not be empty")
        ids = [item.replicate_id for item in self.replicates]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate replicate_id in {self.condition_id}")


@dataclass(frozen=True)
class Project:
    """Portable metadata root for comparisons and downloadable manifests."""

    project_id: str
    title: str
    system_class: SystemClass
    hypothesis: str
    conditions: tuple[Condition, ...]
    evidence_status: str = "preliminary"
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.project_id.strip() or not self.title.strip():
            raise ValueError("project_id and title must not be empty")
        ids = [item.condition_id for item in self.conditions]
        if len(ids) != len(set(ids)):
            raise ValueError("condition_id values must be unique within a project")
        if not self.conditions:
            raise ValueError("a project must contain at least one condition")

    @property
    def replicate_count(self) -> int:
        return sum(len(condition.replicates) for condition in self.conditions)

    def to_manifest(self) -> dict[str, Any]:
        """Return a JSON-ready representation without Python enum objects."""
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "title": self.title,
            "system_class": self.system_class.value,
            "hypothesis": self.hypothesis,
            "evidence_status": self.evidence_status,
            "conditions": [
                {
                    "condition_id": condition.condition_id,
                    "label": condition.label,
                    "variant": condition.variant,
                    "guide_mode": condition.guide_mode.value,
                    "replicates": [
                        {
                            "replicate_id": replicate.replicate_id,
                            "seed": replicate.seed,
                            "trajectory_ns": replicate.trajectory_ns,
                            "analysis_archive": replicate.analysis_archive,
                        }
                        for replicate in condition.replicates
                    ],
                }
                for condition in self.conditions
            ],
        }

    @classmethod
    def from_manifest(cls, data: Mapping[str, Any]) -> "Project":
        """Load project metadata from a previously exported manifest."""
        conditions = tuple(
            Condition(
                condition_id=item["condition_id"],
                label=item["label"],
                variant=item["variant"],
                guide_mode=GuideMode(item.get("guide_mode", "not_applicable")),
                replicates=tuple(Replicate(**rep) for rep in item.get("replicates", [])),
            )
            for item in data["conditions"]
        )
        return cls(
            project_id=data["project_id"],
            title=data["title"],
            system_class=SystemClass(data["system_class"]),
            hypothesis=data.get("hypothesis", ""),
            conditions=conditions,
            evidence_status=data.get("evidence_status", "preliminary"),
            schema_version=int(data.get("schema_version", 1)),
        )

