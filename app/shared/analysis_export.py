"""Build portable StrandMD analysis packages for browser downloads."""
from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from casmd import __version__
from casmd.project import Project
from casmd.report.comparison import ComparisonData
from casmd.report.data import AnalysisResult, AnalysisSummary
from casmd.report.stats import StatTest


_README = """# StrandMD analysis package

This archive contains the numerical data, available figures, and provenance
shown in the StrandMD web dashboard.

## Interpretation limits

- Molecular dynamics frames are autocorrelated and are not independent
  biological replicates.
- Descriptive differences between single trajectories do not establish
  statistical significance.
- Structure prediction and simulation results prioritize hypotheses for
  experimental testing; they do not prove binding affinity or activity.
- Inspect `manifest.json` and `summary.json` before reusing a figure.
"""


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._") or "run"


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, indent=2, allow_nan=False).encode("utf-8")


def _summary_dict(summary: AnalysisSummary) -> dict:
    data = asdict(summary)
    # JSON has no portable NaN representation. Missing/non-finite values are
    # exported as null instead of implementation-specific NaN tokens.
    for key, value in list(data.items()):
        if isinstance(value, float) and value != value:
            data[key] = None
    return data


def build_descriptive_comparison(
    *,
    summary_a: AnalysisSummary,
    summary_b: AnalysisSummary,
    label_a: str,
    label_b: str,
    figures_a: Mapping[str, Path] | None = None,
    figures_b: Mapping[str, Path] | None = None,
) -> ComparisonData:
    """Build scalar, descriptive comparison data without frame-wise tests."""
    scalar_fields = {
        "rmsd": "protein_rmsd_equil_mean_A",
        "rmsf": "protein_rmsf_mean_A",
        "rg": "protein_rg_equil_mean_A",
    }
    stats = {}
    for metric, field in scalar_fields.items():
        value_a = getattr(summary_a, field)
        value_b = getattr(summary_b, field)
        if value_a is None or value_b is None:
            continue
        stats[metric] = StatTest(
            metric=metric,
            mean_a=float(value_a),
            mean_b=float(value_b),
            delta=float(value_b) - float(value_a),
            test_name="descriptive difference",
            pvalue=float("nan"),
            significant=False,
        )

    def _result(summary: AnalysisSummary) -> AnalysisResult:
        return AnalysisResult(
            n_frames=summary.n_frames,
            equil_skip=summary.equil_skip,
            protein_rmsd_equil_mean_A=summary.protein_rmsd_equil_mean_A,
            protein_rmsf_mean_A=summary.protein_rmsf_mean_A,
            protein_rg_equil_mean_A=summary.protein_rg_equil_mean_A,
        )

    return ComparisonData(
        label_a=label_a,
        label_b=label_b,
        analysis_a=_result(summary_a),
        analysis_b=_result(summary_b),
        figures_a=dict(figures_a or {}),
        figures_b=dict(figures_b or {}),
        stats=stats,
        interpretation=(
            "Descriptive trajectory differences only; independent replicates "
            "are required for inferential analysis."
        ),
    )


def _write_run_files(
    zf: zipfile.ZipFile,
    *,
    root: str,
    summary: AnalysisSummary,
    dat_files: Mapping[str, Path],
    fig_files: Mapping[str, Path],
) -> list[str]:
    written = []
    summary_name = f"{root}/summary.json"
    zf.writestr(summary_name, _json_bytes(_summary_dict(summary)))
    written.append(summary_name)

    for key, path in sorted(dat_files.items()):
        path = Path(path)
        if path.exists():
            name = f"{root}/data/{_slug(key)}{path.suffix or '.dat'}"
            zf.writestr(name, path.read_bytes())
            written.append(name)
    for key, path in sorted(fig_files.items()):
        path = Path(path)
        if path.exists():
            name = f"{root}/figures/{_slug(key)}{path.suffix or '.png'}"
            zf.writestr(name, path.read_bytes())
            written.append(name)
    return written


def build_single_analysis_package(
    *,
    label: str,
    summary: AnalysisSummary,
    dat_files: Mapping[str, Path],
    fig_files: Mapping[str, Path],
    project: Project | None = None,
    condition_id: str | None = None,
    replicate_id: str | None = None,
) -> bytes:
    """Return a ZIP containing one run's dashboard data and provenance."""
    output = io.BytesIO()
    root = f"runs/{_slug(label)}"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        written = _write_run_files(
            zf, root=root, summary=summary,
            dat_files=dat_files, fig_files=fig_files,
        )
        manifest = {
            "schema_version": 1,
            "application": "StrandMD",
            "application_version": __version__,
            "package_type": "single_analysis",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "label": label,
            "project_id": project.project_id if project else None,
            "condition_id": condition_id,
            "replicate_id": replicate_id,
            "files": written,
        }
        if project is not None:
            zf.writestr("project.json", _json_bytes(project.to_manifest()))
            written.append("project.json")
        zf.writestr("manifest.json", _json_bytes(manifest))
        zf.writestr("README.md", _README.encode("utf-8"))
    return output.getvalue()


def build_comparison_analysis_package(
    *,
    comparison: ComparisonData,
    summary_a: AnalysisSummary,
    summary_b: AnalysisSummary,
    dat_a: Mapping[str, Path],
    dat_b: Mapping[str, Path],
    fig_a: Mapping[str, Path],
    fig_b: Mapping[str, Path],
    project: Project | None = None,
) -> bytes:
    """Return a ZIP for a descriptive two-run comparison.

    Inferential p-values are deliberately excluded: a pair of autocorrelated
    trajectories does not provide independent replicate-level evidence.
    """
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        written = []
        written += _write_run_files(
            zf, root=f"runs/{_slug(comparison.label_a)}", summary=summary_a,
            dat_files=dat_a, fig_files=fig_a,
        )
        written += _write_run_files(
            zf, root=f"runs/{_slug(comparison.label_b)}", summary=summary_b,
            dat_files=dat_b, fig_files=fig_b,
        )
        descriptive = {
            "label_a": comparison.label_a,
            "label_b": comparison.label_b,
            "note": (
                "Descriptive trajectory differences only. Add independent "
                "replicates before inferential analysis."
            ),
            "metrics": {
                key: {
                    "mean_a": stat.mean_a,
                    "mean_b": stat.mean_b,
                    "delta_b_minus_a": stat.delta,
                }
                for key, stat in comparison.stats.items()
            },
        }
        zf.writestr("comparison_summary.json", _json_bytes(descriptive))
        written.append("comparison_summary.json")
        if project is not None:
            zf.writestr("project.json", _json_bytes(project.to_manifest()))
            written.append("project.json")
        manifest = {
            "schema_version": 1,
            "application": "StrandMD",
            "application_version": __version__,
            "package_type": "descriptive_comparison",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "labels": [comparison.label_a, comparison.label_b],
            "project_id": project.project_id if project else None,
            "files": written,
        }
        zf.writestr("manifest.json", _json_bytes(manifest))
        zf.writestr("README.md", _README.encode("utf-8"))
    return output.getvalue()
