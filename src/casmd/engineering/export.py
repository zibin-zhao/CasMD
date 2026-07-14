"""Portable guided-engineering design packages."""
from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, timezone

from casmd import __version__
from casmd.engineering.models import DesignReport, VariantComparison


def _csv_bytes(rows: list[dict]) -> bytes:
    output = io.StringIO()
    if not rows:
        return b""
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _rationale(report: DesignReport) -> str:
    selected = report.mutation_set.selected
    lines = [
        "# StrandMD guided-engineering rationale",
        "",
        f"**Source:** {report.source_label}",
        f"**Analyzed frames:** {report.n_frames}",
        "",
        "## Engineering objective",
        "",
    ]
    for region in report.config.regions:
        lines.append(
            f"- **{region.label}** — `{region.objective.value}`; "
            f"selection `{region.selection}`; cutoff {region.cutoff_A:g} Å"
        )
    lines += ["", "## Suggested mutation set", ""]
    if selected:
        for candidate in selected:
            lines.append(
                f"- **{candidate.suggested_mutation}** ({candidate.protein.token}): "
                f"score {candidate.design_score:.3f}; target engagement "
                f"{candidate.target_engagement:.1%}; preserve burden "
                f"{candidate.preservation_burden:.1%}; risk {candidate.structural_risk:.2f}."
            )
    else:
        lines.append("- No mutation satisfied the current constraints.")
    lines += [
        "",
        f"Observed target-pair coverage: {report.mutation_set.target_pair_coverage:.1%}.",
        "",
        "## Truncation audits",
        "",
    ]
    if report.truncation_audits:
        for audit in report.truncation_audits:
            lines.append(f"- **{audit.truncation.truncation_id}:** {audit.interpretation}")
    else:
        lines.append("- No truncation was requested.")
    lines += [
        "",
        "## Interpretation limits",
        "",
        "This report ranks trajectory-supported interventions. It does not predict "
        "biochemical activity, binding affinity, expression, solubility, or folding.",
        "",
        "Contact occupancy depends on the supplied selections, cutoff, trajectory "
        "sampling, force field, and equilibration choice. Independent simulation "
        "replicates and wet-lab validation are required.",
        "",
    ]
    return "\n".join(lines)


def build_design_package(
    report: DesignReport,
    *,
    comparison: VariantComparison | None = None,
) -> bytes:
    """Return a ZIP with design evidence, rationale, provenance, and raw tables."""
    fingerprint_rows = [
        {
            "protein_residue": item.protein.token,
            "protein_resname": item.protein.resname,
            "region_id": item.region_id,
            "contact_occupancy": item.contact_occupancy,
            "o2prime_occupancy": item.o2prime_occupancy,
            "mean_contact_distance_A": item.mean_contact_distance_A,
            "p10_contact_distance_A": item.p10_contact_distance_A,
            "contact_events": item.contact_events,
            "longest_run_frames": item.longest_run_frames,
            "nucleotide_coverage": item.nucleotide_coverage,
        }
        for item in report.fingerprints
    ]
    candidate_rows = [
        {
            "protein_residue": item.protein.token,
            "protein_resname": item.protein.resname,
            "suggested_mutation": item.suggested_mutation,
            "target_engagement": item.target_engagement,
            "preservation_burden": item.preservation_burden,
            "structural_risk": item.structural_risk,
            "o2prime_signal": item.o2prime_signal,
            "design_score": item.design_score,
            "eligible": item.eligible,
            "exclusion_reason": item.exclusion_reason,
            "target_pair_count": len(item.target_pairs),
        }
        for item in report.candidates
    ]
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        files = [
            "engineering_config.json",
            "design_report.json",
            "fingerprints.csv",
            "mutation_candidates.csv",
            "RATIONALE.md",
        ]
        zf.writestr(
            "engineering_config.json",
            json.dumps(report.config.to_dict(), indent=2, allow_nan=False),
        )
        zf.writestr("design_report.json", report.to_json())
        zf.writestr("fingerprints.csv", _csv_bytes(fingerprint_rows))
        zf.writestr("mutation_candidates.csv", _csv_bytes(candidate_rows))
        zf.writestr("RATIONALE.md", _rationale(report))
        if comparison is not None:
            zf.writestr(
                "variant_comparison.json",
                json.dumps(comparison.to_dict(), indent=2, allow_nan=False),
            )
            files.append("variant_comparison.json")
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "application": "StrandMD",
                    "application_version": __version__,
                    "package_type": "guided_engineering_design",
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "source_label": report.source_label,
                    "files": files,
                },
                indent=2,
            ),
        )
    return output.getvalue()

