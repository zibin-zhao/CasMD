"""Interpretable mutation, truncation, and variant-design heuristics."""
from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

import numpy as np

from casmd.engineering.models import (
    EngineeringConfig,
    MutationCandidate,
    MutationSet,
    RegionComparison,
    RegionFingerprint,
    RegionObjective,
    TruncationAudit,
    TruncationSpec,
    VariantComparison,
)


_ONE_LETTER = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "HID": "H",
    "HIE": "H", "HIP": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T",
    "TRP": "W", "TYR": "Y", "VAL": "V",
}


def _region_objectives(config: EngineeringConfig) -> dict[str, RegionObjective]:
    return {item.region_id: item.objective for item in config.regions}


def _group_by_protein(
    fingerprints: Sequence[RegionFingerprint],
) -> dict:
    grouped = defaultdict(list)
    for fingerprint in fingerprints:
        grouped[fingerprint.protein].append(fingerprint)
    return grouped


def rank_mutation_candidates(
    config: EngineeringConfig,
    fingerprints: Sequence[RegionFingerprint],
) -> tuple[MutationCandidate, ...]:
    """Rank alanine substitutions while exposing every score component."""
    objectives = _region_objectives(config)
    candidates = []
    for protein, items in _group_by_protein(fingerprints).items():
        target_items = [
            item for item in items
            if objectives.get(item.region_id) == RegionObjective.WEAKEN
        ]
        preserve_items = [
            item for item in items
            if objectives.get(item.region_id) == RegionObjective.PRESERVE
        ]
        target_engagement = sum(item.contact_occupancy for item in target_items)
        preservation_burden = sum(item.contact_occupancy for item in preserve_items)
        o2prime_signal = sum(item.o2prime_occupancy for item in target_items)
        structural_risk = config.risk_for(protein)
        design_score = (
            target_engagement
            + config.o2prime_bonus * o2prime_signal
            - config.preservation_weight * preservation_burden
            - config.risk_weight * structural_risk
        )
        target_pairs = tuple(
            sorted(
                {
                    f"{item.region_id}:{contact.nucleotide.token}"
                    for item in target_items
                    for contact in item.nucleotide_contacts
                    if contact.occupancy >= config.min_occupancy
                }
            )
        )

        one_letter = _ONE_LETTER.get(protein.resname.upper(), "X")
        suggested = f"{one_letter}{protein.resid}A"
        exclusion = ""
        if config.is_protected(protein):
            exclusion = "Residue is protected by the user."
        elif one_letter == "X":
            exclusion = (
                "Residue type is not a supported standard amino acid; "
                "review its chemistry manually."
            )
        elif target_engagement < config.min_occupancy:
            exclusion = "Target-region engagement is below the occupancy threshold."
        elif protein.resname.upper() == "ALA":
            exclusion = "Residue is already alanine."
        elif protein.resname.upper() == "GLY":
            exclusion = "Glycine requires a dedicated backbone-risk review."
        elif protein.resname.upper() == "PRO":
            exclusion = "Proline requires a dedicated backbone-risk review."

        rationale = [
            f"Target-region engagement {target_engagement:.1%}.",
        ]
        if o2prime_signal > 0:
            rationale.append(f"RNA 2-prime-oxygen contact signal {o2prime_signal:.1%}.")
        if preservation_burden > 0:
            rationale.append(
                f"Preserve-region burden {preservation_burden:.1%}; mutation may affect protected function."
            )
        if structural_risk > 0:
            rationale.append(f"User structural-risk penalty {structural_risk:.2f}.")
        if target_pairs:
            rationale.append(f"Covers {len(target_pairs)} target residue/nucleotide pairs.")

        candidates.append(
            MutationCandidate(
                protein=protein,
                suggested_mutation=suggested,
                target_engagement=target_engagement,
                preservation_burden=preservation_burden,
                structural_risk=structural_risk,
                o2prime_signal=o2prime_signal,
                design_score=design_score,
                target_pairs=target_pairs,
                eligible=not exclusion,
                exclusion_reason=exclusion,
                rationale=tuple(rationale),
            )
        )
    return tuple(
        sorted(
            candidates,
            key=lambda item: (-item.design_score, item.protein.segid, item.protein.resid),
        )
    )


def select_mutation_set(
    config: EngineeringConfig,
    candidates: Sequence[MutationCandidate],
) -> MutationSet:
    """Greedily select complementary candidates under preservation/risk limits."""
    all_target_pairs = {pair for item in candidates for pair in item.target_pairs}
    remaining = [
        item for item in candidates
        if item.eligible
        and item.design_score > 0
        and item.preservation_burden <= config.max_preservation_burden
    ]
    selected = []
    covered: set[str] = set()
    cumulative_risk = 0.0
    preservation_burden = 0.0

    while remaining and len(selected) < config.mutation_budget:
        feasible = [
            item for item in remaining
            if cumulative_risk + item.structural_risk <= config.max_cumulative_risk
            and preservation_burden + item.preservation_burden
            <= config.max_preservation_burden
        ]
        if not feasible:
            break

        def utility(item: MutationCandidate) -> tuple[float, float, int]:
            new_pairs = set(item.target_pairs) - covered
            marginal_coverage = (
                len(new_pairs) / len(all_target_pairs) if all_target_pairs else 0.0
            )
            return (
                item.design_score + config.coverage_weight * marginal_coverage,
                item.design_score,
                -item.protein.resid,
            )

        best = max(feasible, key=utility)
        selected.append(best)
        covered.update(best.target_pairs)
        cumulative_risk += best.structural_risk
        preservation_burden += best.preservation_burden
        remaining.remove(best)

    warnings = []
    coverage = len(covered) / len(all_target_pairs) if all_target_pairs else 0.0
    if not selected:
        warnings.append("No eligible mutation satisfies the current constraints.")
    if coverage < 0.5 and all_target_pairs:
        warnings.append("Selected mutations cover less than half of the observed target interface.")
    return MutationSet(
        selected=tuple(selected),
        target_pair_coverage=coverage,
        preservation_burden=preservation_burden,
        cumulative_risk=cumulative_risk,
        warnings=tuple(warnings),
    )


def audit_truncation(
    config: EngineeringConfig,
    fingerprints: Sequence[RegionFingerprint],
    truncation: TruncationSpec,
    *,
    rmsf_by_residue: Mapping[str, float] | None = None,
) -> TruncationAudit:
    """Measure how much target and preserve interaction mass a deletion removes."""
    objectives = _region_objectives(config)
    target_items = [
        item for item in fingerprints
        if objectives.get(item.region_id) == RegionObjective.WEAKEN
    ]
    preserve_items = [
        item for item in fingerprints
        if objectives.get(item.region_id) == RegionObjective.PRESERVE
    ]
    target_total = sum(item.contact_occupancy for item in target_items)
    preserve_total = sum(item.contact_occupancy for item in preserve_items)
    target_removed = sum(
        item.contact_occupancy for item in target_items if truncation.contains(item.protein)
    )
    preserve_removed = sum(
        item.contact_occupancy for item in preserve_items if truncation.contains(item.protein)
    )
    target_coverage = target_removed / target_total if target_total else 0.0
    preserve_coverage = preserve_removed / preserve_total if preserve_total else 0.0
    distributed = target_coverage < config.truncation_coverage_gate

    outside_target = defaultdict(float)
    for item in target_items:
        if not truncation.contains(item.protein):
            outside_target[item.protein.token] += item.contact_occupancy
    remaining = tuple(
        token for token, _ in sorted(outside_target.items(), key=lambda pair: -pair[1])
        if outside_target[token] >= config.min_occupancy
    )

    flexibility_ratio = None
    if rmsf_by_residue:
        inside_values = [
            float(value) for token, value in rmsf_by_residue.items()
            if _token_in_truncation(token, truncation)
        ]
        outside_values = [
            float(value) for token, value in rmsf_by_residue.items()
            if not _token_in_truncation(token, truncation)
        ]
        if inside_values and outside_values and np.mean(outside_values) != 0:
            flexibility_ratio = float(np.mean(inside_values) / np.mean(outside_values))

    if distributed:
        interpretation = (
            f"Deletion removes {target_coverage:.1%} of observed target-region interaction mass; "
            "a distributed interface remains, so deletion alone is unlikely to satisfy the MD objective."
        )
    else:
        interpretation = (
            f"Deletion removes {target_coverage:.1%} of observed target-region interaction mass. "
            "Advance only if preserve-region loss and structural-boundary checks are acceptable."
        )
    return TruncationAudit(
        truncation=truncation,
        target_coverage_removed=target_coverage,
        preserve_coverage_removed=preserve_coverage,
        unwanted_interaction_remaining=max(0.0, 1.0 - target_coverage),
        distributed_interface_warning=distributed,
        remaining_candidate_residues=remaining,
        flexibility_ratio=flexibility_ratio,
        interpretation=interpretation,
    )


def _token_in_truncation(token: str, truncation: TruncationSpec) -> bool:
    try:
        segid, resid_text = token.rsplit(":", 1)
        resid = int(resid_text)
    except (ValueError, AttributeError):
        return False
    segid_matches = not truncation.segid or truncation.segid == "*" or segid == truncation.segid
    return segid_matches and truncation.start_resid <= resid <= truncation.end_resid


def _region_mass(
    fingerprints: Sequence[RegionFingerprint], region_id: str
) -> float:
    pair_mass = sum(
        contact.occupancy
        for item in fingerprints
        if item.region_id == region_id
        for contact in item.nucleotide_contacts
    )
    if pair_mass:
        return pair_mass
    return sum(
        item.contact_occupancy for item in fingerprints if item.region_id == region_id
    )


def compare_variants(
    config: EngineeringConfig,
    baseline: Sequence[RegionFingerprint],
    variant: Sequence[RegionFingerprint],
    baseline_label: str,
    variant_label: str,
) -> VariantComparison:
    """Compare region interaction mass according to each configured objective."""
    comparisons = []
    for region in config.regions:
        baseline_mass = _region_mass(baseline, region.region_id)
        variant_mass = _region_mass(variant, region.region_id)
        if baseline_mass > 0:
            retention = variant_mass / baseline_mass * 100.0
            if region.objective == RegionObjective.WEAKEN:
                objective_change = 1.0 - variant_mass / baseline_mass
            elif region.objective == RegionObjective.PRESERVE:
                objective_change = variant_mass / baseline_mass
            else:
                objective_change = variant_mass / baseline_mass - 1.0
        else:
            retention = None
            objective_change = None
        comparisons.append(
            RegionComparison(
                region_id=region.region_id,
                objective=region.objective,
                baseline_mass=baseline_mass,
                variant_mass=variant_mass,
                retention_pct=retention,
                objective_change=objective_change,
            )
        )
    return VariantComparison(
        baseline_label=baseline_label,
        variant_label=variant_label,
        regions=tuple(comparisons),
    )
