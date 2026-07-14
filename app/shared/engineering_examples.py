"""Fully fictional guided-engineering data for the public tutorial."""
from __future__ import annotations

from casmd.engineering.io import build_design_report
from casmd.engineering.models import (
    EngineeringConfig,
    NucleotideContact,
    RegionFingerprint,
    RegionObjective,
    RegionSpec,
    ResidueKey,
    TruncationSpec,
)


TUTORIAL_CONFIG = EngineeringConfig(
    protein_selection="segid A",
    regions=(
        RegionSpec(
            "target_region",
            "Fictional RNA target segment",
            "segid B and resid 5:16",
            RegionObjective.WEAKEN,
            4.0,
        ),
        RegionSpec(
            "protected_region",
            "Fictional RNA functional segment",
            "segid B and resid 17:30",
            RegionObjective.PRESERVE,
            4.0,
        ),
    ),
    mutation_budget=5,
    min_occupancy=0.05,
    preservation_weight=1.0,
    risk_weight=1.0,
    o2prime_bonus=0.25,
    max_preservation_burden=0.45,
    truncations=(TruncationSpec("Fictional flexible loop", "A", 230, 276),),
)


def _fp(resid, resname, region, occupancy, pairs, *, o2=0.0):
    return RegionFingerprint(
        protein=ResidueKey("A", resid, resname),
        region_id=region,
        contact_occupancy=occupancy,
        mean_contact_distance_A=3.35,
        p10_contact_distance_A=2.95,
        contact_events=12,
        longest_run_frames=85,
        o2prime_occupancy=o2,
        nucleotide_contacts=tuple(
            NucleotideContact(ResidueKey("B", nucleotide, "A"), pair_occupancy)
            for nucleotide, pair_occupancy in pairs
        ),
    )


_REFERENCE_FINGERPRINTS = (
    _fp(112, "ARG", "target_region", 0.86, ((5, 0.74), (6, 0.61)), o2=0.31),
    _fp(112, "ARG", "protected_region", 0.06, ((17, 0.06),)),
    _fp(176, "ASN", "target_region", 0.72, ((7, 0.63),), o2=0.27),
    _fp(245, "ARG", "target_region", 0.18, ((8, 0.18),), o2=0.03),
    _fp(245, "ARG", "protected_region", 0.10, ((18, 0.10),)),
    _fp(318, "LEU", "target_region", 0.22, ((9, 0.20),)),
    _fp(318, "LEU", "protected_region", 0.68, ((19, 0.62),)),
    _fp(362, "TYR", "target_region", 0.78, ((10, 0.70), (11, 0.52)), o2=0.44),
    _fp(362, "TYR", "protected_region", 0.04, ((20, 0.04),)),
    _fp(409, "ASP", "target_region", 0.69, ((12, 0.61),), o2=0.39),
    _fp(455, "LYS", "target_region", 0.58, ((13, 0.50),)),
    _fp(455, "LYS", "protected_region", 0.12, ((21, 0.11),)),
)


_VARIANT_A_FINGERPRINTS = (
    _fp(112, "ALA", "target_region", 0.13, ((5, 0.11),), o2=0.02),
    _fp(112, "ALA", "protected_region", 0.05, ((17, 0.05),)),
    _fp(176, "ALA", "target_region", 0.11, ((7, 0.09),), o2=0.02),
    _fp(318, "ALA", "target_region", 0.09, ((9, 0.08),)),
    _fp(318, "ALA", "protected_region", 0.61, ((19, 0.56),)),
    _fp(362, "ALA", "target_region", 0.12, ((10, 0.10),), o2=0.02),
    _fp(362, "ALA", "protected_region", 0.04, ((20, 0.04),)),
    _fp(409, "ALA", "target_region", 0.10, ((12, 0.08),), o2=0.01),
    _fp(455, "ALA", "target_region", 0.16, ((13, 0.14),)),
    _fp(455, "ALA", "protected_region", 0.11, ((21, 0.10),)),
)


def load_synthetic_engineering_tutorial():
    """Return reference and Variant A reports made entirely from invented values."""
    provenance = {
        "data_status": "fictional_synthetic_tutorial",
        "notice": (
            "Fictional construct, residue numbering, and measurements. This tutorial "
            "is not derived from an unpublished project."
        ),
    }
    baseline = build_design_report(
        config=TUTORIAL_CONFIG,
        fingerprints=_REFERENCE_FINGERPRINTS,
        n_frames=1000,
        frame_interval_ps=100.0,
        source_label="Fictional reference",
        provenance=provenance,
        rmsf_by_residue={"A:245": 3.2, "A:112": 1.2, "A:362": 1.3},
    )
    variant = build_design_report(
        config=TUTORIAL_CONFIG,
        fingerprints=_VARIANT_A_FINGERPRINTS,
        n_frames=1000,
        frame_interval_ps=100.0,
        source_label="Fictional Variant A",
        provenance=provenance,
    )
    return baseline, variant
