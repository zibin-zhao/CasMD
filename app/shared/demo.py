"""Pre-baked example analysis for the homepage '▶ Run demo' CTA."""
from __future__ import annotations
from pathlib import Path

from casmd.report.data import AnalysisSummary, load_analysis_json


_DEMO_DIR = Path(__file__).resolve().parent.parent / "assets" / "demo"


def load_demo_analysis() -> tuple[AnalysisSummary, dict[str, Path], dict[str, Path]]:
    """Return (summary, dat_files, fig_files) for the bundled example.

    Mirrors Stage 2's existing `_unpack_zip` output shape so it can be
    dropped directly into the same render path."""
    summary = load_analysis_json(_DEMO_DIR / "results.json")
    dat_files = {
        key: _DEMO_DIR / f"{key}.dat"
        for key in ("rmsd", "rmsf", "rg")
        if (_DEMO_DIR / f"{key}.dat").exists()
    }
    fig_files = {
        key: _DEMO_DIR / "figures" / f"{key}.png"
        for key in ("rmsd", "rmsf", "rg")
        if (_DEMO_DIR / "figures" / f"{key}.png").exists()
    }
    return summary, dat_files, fig_files
