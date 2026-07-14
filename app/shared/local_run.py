"""Streamlit helpers for the Stage 1 'Run locally' panel.

Only rendered when the env var CASMD_LOCAL_RUN_ENABLED=1 — i.e. inside the
casmd-full Docker image (which sets that var). The casmd:dev image (and the
public HF Space) leave it unset, so users on the hosted Space only see the
'Download bundle for HPC' button.
"""
from __future__ import annotations
import os
from pathlib import Path

from casmd.run.gpu_check import GpuInfo, detect_gpu, format_eta
from casmd.run.runner import run_md_locally


def is_local_run_enabled() -> bool:
    """True if running inside casmd-full (i.e. GROMACS is present)."""
    return os.environ.get("CASMD_LOCAL_RUN_ENABLED", "0") == "1"


def build_eta_summary(gpu: GpuInfo, production_ns: float) -> str:
    """One-line wall-time estimate for the picker."""
    hours = production_ns * 24 / max(gpu.est_ns_per_day, 0.1)
    return (
        f"On **{gpu.name}** (~{gpu.est_ns_per_day:.0f} ns/day): "
        f"{production_ns:g} ns ≈ {format_eta(hours)}. "
        f"{gpu.recommendation}"
    )


def render_local_run_panel(*, bundle_dir: Path, default_ns: float = 50.0) -> None:
    """Render the 'Run locally' panel below Stage 1's Build step.

    bundle_dir: directory where Stage 1 unzipped/built the bundle.
    """
    import streamlit as st

    st.markdown("#### Run MD locally (inside this container)")
    st.caption(
        "Runs the full pipeline (em → NVT → NPT → production → analyze.py) "
        "right here. For HPC users, the **Download bundle** button above is "
        "still the recommended path."
    )

    gpu = detect_gpu()
    if gpu.kind == "nvidia":
        st.success(f"🟢 GPU detected: {gpu.name} ({gpu.vram_gb} GB VRAM)")
    elif gpu.kind == "apple":
        st.warning("🟡 Apple Silicon — GROMACS will run CPU-only "
                    "(no Metal backend yet). Short runs only.")
    else:
        st.warning("🟡 No NVIDIA GPU detected — runs will be slow on CPU.")

    ns = st.slider(
        "Production length (ns)",
        min_value=10.0, max_value=300.0,
        value=float(default_ns), step=10.0,
        help=("50 ns is the default for pre-experimental screening. "
              "300 ns is publication-tier."),
    )

    st.info(build_eta_summary(gpu, production_ns=ns))

    if st.button("🚀 Run MD now", type="primary", use_container_width=True,
                  key="local_run_btn"):
        progress_events: list = []

        def _on_progress(evt) -> None:
            progress_events.append(evt)

        with st.status(f"Running MD ({ns:g} ns) — this may take "
                        f"{format_eta(ns * 24 / max(gpu.est_ns_per_day, 0.1))}",
                        expanded=True) as status:
            try:
                st.write(f"• Starting GROMACS in `{bundle_dir}`...")
                result = run_md_locally(
                    bundle_dir=bundle_dir, production_ns=ns,
                    on_progress=_on_progress,
                )
                if result.exit_code == 0:
                    status.update(
                        label=f"✓ MD complete ({result.wall_time_seconds/60:.0f} min)",
                        state="complete", expanded=False,
                    )
                    st.success(
                        "Analysis output in `analysis/`. Go to Stage 2 to "
                        "visualize."
                    )
                else:
                    status.update(label=f"✗ MD failed (exit {result.exit_code})",
                                  state="error", expanded=True)
                    st.error(f"GROMACS exited with code {result.exit_code}. "
                             f"Check `{result.log_path}` for details.")
            except Exception as exc:
                status.update(label="✗ Run failed", state="error", expanded=True)
                st.error(f"Local run failed: {exc}")
