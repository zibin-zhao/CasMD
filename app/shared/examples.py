"""Fully fictional example content shown in the public StrandMD UI."""
from __future__ import annotations

from casmd.project import Condition, GuideMode, Project, Replicate, SystemClass


VARIANT_PROJECT = Project(
    project_id="fictional-variant-a",
    title="Fictional Variant A interface-engineering tutorial",
    system_class=SystemClass.PROTEIN_NUCLEIC_ACID_TERNARY,
    hypothesis=(
        "Can a designed protein variant weaken one RNA interface while preserving "
        "global stability and a protected protein–nucleic-acid interface?"
    ),
    conditions=tuple(
        Condition(
            condition_id=f"{variant.lower().replace(' ', '-')}-{mode.value.lower()}",
            label=f"{variant} · {mode.value}",
            variant=variant,
            guide_mode=mode,
            replicates=(Replicate("run-1"),),
        )
        for variant, modes in (
            ("Reference", (GuideMode.RNA, GuideMode.DNA)),
            ("Loop control", (GuideMode.RNA,)),
            ("Linker control", (GuideMode.RNA,)),
            ("Variant A", (GuideMode.RNA, GuideMode.DNA)),
        )
        for mode in modes
    ),
    evidence_status="fictional_synthetic_tutorial",
)


VARIANT_CONSTRUCTS = [
    {
        "Construct": "Reference",
        "Engineering": "Fictional full-length reference",
        "Role": "Global-stability and interface reference",
    },
    {
        "Construct": "Loop control",
        "Engineering": "Invented loop edit",
        "Role": "Tests whether the loop edit alone changes the target interface",
    },
    {
        "Construct": "Linker control",
        "Engineering": "Invented loop edit with neutral linker",
        "Role": "Controls for geometry restoration",
    },
    {
        "Construct": "Variant A",
        "Engineering": "Invented interface substitutions",
        "Role": "Fictional optimization candidate",
    },
]


VARIANT_METRICS = [
    {
        "Synthetic metric": "Protein Cα RMSD",
        "Reference": "2.40 ± 0.18 Å",
        "Variant A": "2.47 ± 0.20 Å",
        "Illustrative interpretation": "Similar simulated global stability",
    },
    {
        "Synthetic metric": "Radius of gyration",
        "Reference": "34.8 ± 0.2 Å",
        "Variant A": "34.6 ± 0.2 Å",
        "Illustrative interpretation": "Comparable compactness",
    },
    {
        "Synthetic metric": "Target-region contacts",
        "Reference": "1000 ± 40",
        "Variant A": "420 ± 30",
        "Illustrative interpretation": "42% retained",
    },
    {
        "Synthetic metric": "Protected-region contacts",
        "Reference": "1200 ± 35",
        "Variant A": "1050 ± 32",
        "Illustrative interpretation": "88% retained",
    },
    {
        "Synthetic metric": "Second-guide contacts",
        "Reference": "1500 ± 45",
        "Variant A": "1470 ± 41",
        "Illustrative interpretation": "98% retained",
    },
]


VARIANT_RETENTION = {
    "Target-region contacts": 42,
    "Protected-region contacts": 88,
    "Second-guide contacts": 98,
}


CONTROL_RETENTION = {
    "Reference": 100,
    "Loop control": 94,
    "Linker control": 90,
    "Variant A": 42,
}
