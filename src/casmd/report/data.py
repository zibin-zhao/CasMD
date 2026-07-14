"""Data classes for an CasMD report + JSON loader."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PredictionSummary:
    backend: str
    model_id: int
    iptm: float | None
    ptm: float | None
    plddt_mean: float | None


@dataclass(frozen=True)
class AnalysisSummary:
    n_frames: int
    equil_skip: int
    protein_rmsd_equil_mean_A: float | None
    protein_rmsd_max_A: float | None
    protein_rmsf_mean_A: float | None
    protein_rg_equil_mean_A: float | None


@dataclass(frozen=True)
class ReportData:
    job_name: str
    production_ns: float
    prediction: PredictionSummary | None
    analysis: AnalysisSummary
    figures: dict[str, Path]
    interpretation: str


@dataclass
class AnalysisResult:
    """Extended analysis result for comparison workflows.

    Mirrors the scalar fields of AnalysisSummary but omits protein_rmsd_max_A
    (not needed for comparison) and adds optional per-frame series fields so
    that statistical tests (Welch's t-test, KS) can operate on raw data.
    """
    n_frames: int
    equil_skip: int
    protein_rmsd_equil_mean_A: float | None
    protein_rmsf_mean_A: float | None
    protein_rg_equil_mean_A: float | None
    # Optional per-frame series — None when loaded from legacy results.json
    rmsd_series: list[float] | None = None
    rmsf_series: list[float] | None = None
    rg_series: list[float] | None = None


def load_analysis_json(path: Path) -> AnalysisSummary:
    """Parse the `results.json` produced by Plan 3's templated analyze.py."""
    path = Path(path)
    data = json.loads(path.read_text())
    rmsd = data.get("protein_rmsd_A", {})
    rg = data.get("protein_rg_A", {})
    return AnalysisSummary(
        n_frames=int(data.get("n_frames", 0)),
        equil_skip=int(data.get("equil_skip", 0)),
        protein_rmsd_equil_mean_A=_maybe_float(rmsd.get("equilibrated_mean")),
        protein_rmsd_max_A=_maybe_float(rmsd.get("max")),
        protein_rmsf_mean_A=_maybe_float(data.get("protein_rmsf_A_mean")),
        protein_rg_equil_mean_A=_maybe_float(rg.get("equilibrated_mean")),
    )


def _maybe_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
