"""Two-trajectory comparison data structure + builder."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from casmd.report.data import AnalysisResult
from casmd.report.align import ResidueAlignment
from casmd.report.stats import StatTest


@dataclass
class ComparisonData:
    """Bundle of two trajectories' analysis + alignment + stat tests."""
    label_a: str
    label_b: str
    analysis_a: AnalysisResult
    analysis_b: AnalysisResult
    figures_a: dict[str, Path] = field(default_factory=dict)
    figures_b: dict[str, Path] = field(default_factory=dict)
    residue_map: ResidueAlignment | None = None
    stats: dict[str, StatTest] = field(default_factory=dict)
    interpretation: str = ""


from casmd.report.align import sequence_align
from casmd.report.stats import ks_test, welch_test


def build_comparison(
    *,
    analysis_a: AnalysisResult,
    analysis_b: AnalysisResult,
    label_a: str = "Run A",
    label_b: str = "Run B",
    seq_a: str | None = None,
    seq_b: str | None = None,
    figures_a: dict[str, Path] | None = None,
    figures_b: dict[str, Path] | None = None,
    interpretation: str = "",
) -> ComparisonData:
    """Build a ComparisonData from two AnalysisResult instances.

    - Runs Welch's t-test on each metric (RMSD / RMSF / Rg) using the per-series
      values stored in AnalysisResult; falls back to a single-point comparison
      using the mean if a series is missing.
    - Runs sequence alignment if both seq_a and seq_b are provided.
    """
    stats: dict[str, StatTest] = {}

    for key in ("rmsd", "rmsf", "rg"):
        ser_a = getattr(analysis_a, f"{key}_series")
        ser_b = getattr(analysis_b, f"{key}_series")
        if ser_a is not None and ser_b is not None and len(ser_a) > 1 and len(ser_b) > 1:
            stats[key] = welch_test(key, ser_a, ser_b)
        else:
            mean_attr = {
                "rmsd": "protein_rmsd_equil_mean_A",
                "rmsf": "protein_rmsf_mean_A",
                "rg":   "protein_rg_equil_mean_A",
            }[key]
            mean_a = getattr(analysis_a, mean_attr) or 0.0
            mean_b = getattr(analysis_b, mean_attr) or 0.0
            stats[key] = StatTest(
                metric=key,
                mean_a=float(mean_a), mean_b=float(mean_b),
                delta=float(mean_b) - float(mean_a),
                test_name="mean only (no series)",
                pvalue=float("nan"),
                significant=False,
            )

    residue_map = None
    if seq_a and seq_b:
        residue_map = sequence_align(seq_a, seq_b)

    return ComparisonData(
        label_a=label_a,
        label_b=label_b,
        analysis_a=analysis_a,
        analysis_b=analysis_b,
        figures_a=figures_a or {},
        figures_b=figures_b or {},
        residue_map=residue_map,
        stats=stats,
        interpretation=interpretation,
    )
