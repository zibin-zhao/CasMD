"""StrandMD analysis dashboard for one run or a descriptive comparison."""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st
import numpy as np

from app.shared import state
from app.shared.styles import inject_css, card, kpi
from app.shared.viz import parse_dat_file, plot_xy, plot_overlay, plot_delta

from casmd.report.data import load_analysis_json
from app.shared.analysis_export import (
    build_descriptive_comparison,
    build_comparison_analysis_package,
    build_single_analysis_package,
)


inject_css()

# ---- Privacy gate ----
if not state.is_privacy_acked(st.session_state):
    st.warning("Please acknowledge the privacy disclaimer on the landing page first.")
    st.markdown("[← back to landing](/)")
    st.stop()

st.title("Analyze & Compare")
st.markdown(
    "<p style='opacity:0.75'>Upload the lightweight analysis archive produced "
    "beside your trajectory. Explore one run or compare two runs descriptively.</p>",
    unsafe_allow_html=True,
)

# Demo banner + auto-load when the homepage CTA was used
if st.session_state.get("use_demo_data"):
    st.info("**Viewing example data** — synthetic 500 ns tri-complex run. "
            "Real uploads work the same way.", icon="🧪")


def _unpack_zip(uploaded) -> tuple[object | None, dict[str, Path], dict[str, Path]]:
    """Returns (analysis, dat_files, fig_files) for a single uploaded archive
    (zip / 7z / tar / tar.gz)."""
    from app.shared.archive import extract_archive
    analysis = None
    dat_files: dict[str, Path] = {}
    fig_files: dict[str, Path] = {}
    if uploaded is None:
        return analysis, dat_files, fig_files
    try:
        unpack = Path(tempfile.mkdtemp(prefix="casmd_viz_"))
        extract_archive(uploaded.read(), unpack, uploaded.name)
        for candidate in unpack.rglob("results.json"):
            analysis = load_analysis_json(candidate)
            break
        for key in ("rmsd", "rmsf", "rg"):
            for p in unpack.rglob(f"{key}.dat"):
                dat_files[key] = p
                break
            for p in unpack.rglob(f"{key}.png"):
                fig_files[key] = p
                break
    except Exception as e:
        from app.shared.errors import friendly_error
        st.error(friendly_error(e, context="upload"))
    return analysis, dat_files, fig_files


# ---- 1. Uploads ----
from app.shared.archive import SUPPORTED_UPLOAD_TYPES
zip_a = st.file_uploader("Analysis output A", type=SUPPORTED_UPLOAD_TYPES, key="viz_upload_a")

with st.expander("➕ Add second trajectory to compare", expanded=False):
    zip_b = st.file_uploader("Analysis output B", type=SUPPORTED_UPLOAD_TYPES, key="viz_upload_b")
    label_a = st.text_input("Label A", value="Run A", key="cmp_label_a")
    label_b = st.text_input("Label B", value="Run B", key="cmp_label_b")

# Demo override: if the user clicked "▶ Run demo", use the bundled
# analysis. They can still drop a real upload to take over.
if st.session_state.get("use_demo_data") and zip_a is None and zip_b is None:
    from app.shared.demo import load_demo_analysis
    analysis_a, dat_a, fig_a = load_demo_analysis()
    analysis_b, dat_b, fig_b = None, {}, {}
else:
    analysis_a, dat_a, fig_a = _unpack_zip(zip_a)
    analysis_b, dat_b, fig_b = _unpack_zip(zip_b)

# ---- 2. Prediction confidence (from Stage 1 session state) ----
# Shown regardless of whether a zip is uploaded, matching original behavior.
prediction = st.session_state.get("best_prediction")
if prediction:
    st.header("Prediction confidence")
    cols = st.columns(4)
    with cols[0]:
        card(kpi(prediction["backend"].upper(), "Backend"))
    with cols[1]:
        card(kpi(f"{prediction['iptm']:.3f}" if prediction.get("iptm") else "--", "iPTM"))
    with cols[2]:
        card(kpi(f"{prediction['ptm']:.3f}" if prediction.get("ptm") else "--", "pTM"))
    with cols[3]:
        val = prediction.get("plddt_mean")
        if val is not None and val > 1.5:
            display = f"{val:.1f}"
        elif val is not None:
            display = f"{val:.3f}"
        else:
            display = "--"
        card(kpi(display, "pLDDT (mean)"))

# ---- 3. Single-trajectory mode (analysis_a only) ----
if analysis_a is None:
    st.info("Upload an analysis zip above to see the dashboard.")
    st.stop()

if analysis_b is None:
    # Existing single-trajectory dashboard — unchanged behavior.
    st.header("Trajectory metrics")
    cols = st.columns(5)

    def _fmt(v):
        return f"{v:.2f}" if v is not None else "--"

    with cols[0]:
        card(kpi(str(analysis_a.n_frames), "Frames"))
    with cols[1]:
        card(kpi(str(analysis_a.equil_skip), "Equil. discard (frames)"))
    with cols[2]:
        card(kpi(_fmt(analysis_a.protein_rmsd_equil_mean_A) + " Å",
                  "RMSD (equil. mean)"), accent=True)
    with cols[3]:
        card(kpi(_fmt(analysis_a.protein_rmsf_mean_A) + " Å", "RMSF (mean)"))
    with cols[4]:
        card(kpi(_fmt(analysis_a.protein_rg_equil_mean_A) + " Å", "Rg (equil. mean)"))

    st.header("Dynamics")
    plot_specs = [
        ("rmsd", "Protein Cα RMSD", "time (ns)", "RMSD (Å)"),
        ("rmsf", "Per-residue RMSF",  "residue",   "RMSF (Å)"),
        ("rg",   "Radius of gyration", "time (ns)", "Rg (Å)"),
    ]
    plot_cols = st.columns(3)
    for col, (key, title, xlab, ylab) in zip(plot_cols, plot_specs):
        with col:
            if key in dat_a:
                x, y = parse_dat_file(dat_a[key])
                fig = plot_xy(x, y, title=title, x_label=xlab, y_label=ylab)
                st.plotly_chart(fig, width="stretch")
            elif key in fig_a:
                st.image(str(fig_a[key]), caption=title, width="stretch")
            else:
                st.warning(f"No {key}.dat or {key}.png found in the upload.")

    st.header("Download")
    run_label = st.text_input(
        "Run label",
        value=st.session_state.get(state.JOB_NAME, "strandmd_run"),
        key="viz_run_label",
    )
    package = build_single_analysis_package(
        label=run_label, summary=analysis_a,
        dat_files=dat_a, fig_files=fig_a,
    )
    st.download_button(
        "⬇ Download complete analysis package",
        package,
        file_name=f"{run_label.replace(' ', '_')}_analysis.zip",
        mime="application/zip",
        type="primary",
        width="stretch",
    )
    st.caption(
        "Includes summary JSON, numerical plot data, available figures, "
        "provenance, methods notes, and interpretation limits."
    )
    st.stop()

cd = build_descriptive_comparison(
    summary_a=analysis_a, summary_b=analysis_b,
    label_a=label_a, label_b=label_b,
    figures_a=fig_a, figures_b=fig_b,
)

# Summary table — descriptive only until independent replicates are supplied.
st.header(f"{label_a} vs {label_b} — summary")
st.warning(
    "This two-run view is descriptive. MD frames are autocorrelated and do "
    "not replace independent simulation replicates; inferential p-values are "
    "therefore not shown."
)
metric_cols = st.columns(4)
metric_cols[0].markdown("**Metric**")
metric_cols[1].markdown(f"**{label_a}**")
metric_cols[2].markdown(f"**{label_b}**")
metric_cols[3].markdown("**Δ (B − A)**")

for key, stat in cd.stats.items():
    r = st.columns(4)
    r[0].markdown(f"**{key.upper()}**")
    r[1].markdown(f"{stat.mean_a:.2f}")
    r[2].markdown(f"{stat.mean_b:.2f}")
    r[3].markdown(f"{stat.delta:+.2f}")

# Overlay plots
st.header("Dynamics — overlay")
plot_specs = [
    ("rmsd", "RMSD over time",         "time (ns)", "RMSD (Å)"),
    ("rmsf", "RMSF per residue",       "residue",   "RMSF (Å)"),
    ("rg",   "Radius of gyration",     "time (ns)", "Rg (Å)"),
]
residue_axes_confirmed = st.checkbox(
    "The two RMSF files use the same protein residue identities and numbering",
    value=False,
    help=(
        "Leave this unchecked for truncations, insertions, or renumbered models. "
        "A gap-aware residue map will be required before those profiles can be overlaid."
    ),
)
for key, title, xlab, ylab in plot_specs:
    st.subheader(title)
    cols = st.columns([2, 1])
    if key in dat_a and key in dat_b:
        xa, ya = parse_dat_file(dat_a[key])
        xb, yb = parse_dat_file(dat_b[key])
        if key == "rmsf" and not residue_axes_confirmed:
            st.warning(
                "RMSF overlay is paused until residue identity equivalence is "
                "confirmed. Truncation comparisons require gap-aware mapping."
            )
            continue
        if key == "rmsf" and not np.array_equal(xa, xb):
            st.warning("Residue axes differ; a gap-aware residue map is required.")
            continue

        if key in ("rmsd", "rg"):
            xa = xa[analysis_a.equil_skip:]
            ya = ya[analysis_a.equil_skip:]
            xb = xb[analysis_b.equil_skip:]
            yb = yb[analysis_b.equil_skip:]

        if key in ("rmsd", "rg") and not np.array_equal(xa, xb):
            # Interpolate B onto A within the shared physical time interval.
            mask = (xa >= max(xa.min(), xb.min())) & (xa <= min(xa.max(), xb.max()))
            x_plot = xa[mask]
            y_a_plot = ya[mask]
            y_b_plot = np.interp(x_plot, xb, yb)
        else:
            x_plot = xa
            y_a_plot = ya
            y_b_plot = yb
        with cols[0]:
            overlay = plot_overlay(
                x=x_plot, y_a=y_a_plot, y_b=y_b_plot,
                label_a=label_a, label_b=label_b,
                title=title, x_label=xlab, y_label=ylab,
            )
            st.plotly_chart(overlay, width="stretch")
            delta = y_b_plot - y_a_plot
            delta_fig = plot_delta(
                x=x_plot, delta=delta, title=f"Δ {key.upper()}",
                x_label=xlab, y_label=f"Δ {ylab}",
            )
            st.plotly_chart(delta_fig, width="stretch")
        with cols[1]:
            stat = cd.stats.get(key)
            if stat is not None:
                st.markdown(
                    "**Descriptive difference**  \n"
                    f"{label_a}: {stat.mean_a:.2f}  \n"
                    f"{label_b}: {stat.mean_b:.2f}  \n"
                    f"Δ mean: {stat.delta:+.2f}"
                )
    else:
        st.warning(f"{key}.dat missing in one of the uploads — skipping overlay.")

# Comparison package download
st.header("Download")
cmp_job = st.text_input(
    "Comparison label", value=f"{label_a}_vs_{label_b}".replace(" ", "_"),
    key="cmp_job_name",
)
comparison_package = build_comparison_analysis_package(
    comparison=cd,
    summary_a=analysis_a,
    summary_b=analysis_b,
    dat_a=dat_a,
    dat_b=dat_b,
    fig_a=fig_a,
    fig_b=fig_b,
)
st.download_button(
    "⬇ Download complete comparison package",
    comparison_package,
    file_name=f"{cmp_job}_analysis.zip",
    mime="application/zip",
    type="primary",
    width="stretch",
)

from app.shared.footer import render_footer
render_footer()
