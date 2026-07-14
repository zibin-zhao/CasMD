"""Stage 2 — viz dashboard for analyze.py outputs + optional report download."""
from __future__ import annotations
# Ensure repo root is on sys.path for `from app.shared import ...` when
# Streamlit loads this page file directly.
import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import io
import json
import tempfile
import zipfile

import streamlit as st

from app.shared import state
from app.shared.styles import inject_css, card, kpi
from app.shared.viz import parse_dat_file, plot_xy

from hsingmd.report.data import (
    PredictionSummary, ReportData, load_analysis_json,
)
from hsingmd.report.docx_writer import generate_docx
from hsingmd.report.pptx_writer import generate_pptx


st.set_page_config(page_title="HsingMD — Results & Viz", page_icon="📊", layout="wide")
inject_css()

# ---- Privacy gate ----
if not state.is_privacy_acked(st.session_state):
    st.warning("Please acknowledge the privacy disclaimer on the landing page first.")
    st.markdown("[← back to landing](/)")
    st.stop()

st.title("Stage 2 — Results & Visualization")
st.markdown(
    "<p style='opacity:0.75'>Upload <code>analyze.py</code>'s output dir as a zip "
    "(should contain <code>results.json</code>, <code>rmsd.dat</code>, "
    "<code>rmsf.dat</code>, <code>rg.dat</code>, and <code>figures/</code>).</p>",
    unsafe_allow_html=True,
)

# ---- 1. Upload ----
upload = st.file_uploader("Analysis output (.zip)", type="zip", key="viz_upload")

# Parse upload if present
analysis = None
dat_files: dict[str, Path] = {}
fig_files: dict[str, Path] = {}
if upload is not None:
    try:
        unpack = Path(tempfile.mkdtemp(prefix="hsingmd_viz_"))
        with zipfile.ZipFile(io.BytesIO(upload.read())) as zf:
            zf.extractall(unpack)
        # Find results.json anywhere in the unpacked tree
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
        st.error(f"Could not parse upload: {e}")

# ---- 2. Prediction confidence (from Stage 1 session state) ----
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
        # Some backends use 0-1 scale, others 0-100. Normalize for display.
        if val is not None and val > 1.5:
            display = f"{val:.1f}"
        elif val is not None:
            display = f"{val:.3f}"
        else:
            display = "--"
        card(kpi(display, "pLDDT (mean)"))

# ---- 3. Trajectory KPI cards ----
if analysis is None:
    st.info("Upload an analysis zip above to see the dashboard.")
    st.stop()

st.header("Trajectory metrics")
cols = st.columns(5)


def _fmt(v):
    return f"{v:.2f}" if v is not None else "--"


with cols[0]:
    card(kpi(str(analysis.n_frames), "Frames"))
with cols[1]:
    card(kpi(str(analysis.equil_skip), "Equil. discard (frames)"))
with cols[2]:
    card(kpi(_fmt(analysis.protein_rmsd_equil_mean_A) + " Å",
              "RMSD (equil. mean)"), accent=True)
with cols[3]:
    card(kpi(_fmt(analysis.protein_rmsf_mean_A) + " Å", "RMSF (mean)"))
with cols[4]:
    card(kpi(_fmt(analysis.protein_rg_equil_mean_A) + " Å", "Rg (equil. mean)"))

# ---- 4. Interactive plots ----
st.header("Dynamics")

plot_specs = [
    ("rmsd", "Protein Cα RMSD", "time (ns)", "RMSD (Å)"),
    ("rmsf", "Per-residue RMSF",  "residue",   "RMSF (Å)"),
    ("rg",   "Radius of gyration", "time (ns)", "Rg (Å)"),
]

plot_cols = st.columns(3)
for col, (key, title, xlab, ylab) in zip(plot_cols, plot_specs):
    with col:
        if key in dat_files:
            x, y = parse_dat_file(dat_files[key])
            fig = plot_xy(x, y, title=title, x_label=xlab, y_label=ylab)
            st.plotly_chart(fig, use_container_width=True)
        elif key in fig_files:
            # Fallback to the PNG figure if only .png is available
            st.image(str(fig_files[key]), caption=title, use_container_width=True)
        else:
            st.warning(f"No {key}.dat or {key}.png found in the upload.")

# ---- 5. Interpretation + Download buttons ----
st.header("Report")
job_name = st.text_input("Job name for the exported report",
                         value=st.session_state.get(state.JOB_NAME, "hsingmd_run"),
                         key="viz_job_name")
production_ns = st.number_input("Production length (ns)", min_value=1.0, value=100.0,
                                step=10.0, key="viz_prod_ns")
interpretation = st.text_area(
    "Interpretation paragraph (plain English)", height=100, key="viz_interp",
    value=("Protein backbone stable across the trajectory; metrics within expected ranges."),
)


def _build_report_data() -> ReportData:
    pred = None
    if prediction:
        pred = PredictionSummary(
            backend=prediction["backend"], model_id=prediction["model_id"],
            iptm=prediction.get("iptm"), ptm=prediction.get("ptm"),
            plddt_mean=prediction.get("plddt_mean"),
        )
    return ReportData(
        job_name=job_name,
        production_ns=float(production_ns),
        prediction=pred,
        analysis=analysis,
        figures=fig_files,
        interpretation=interpretation,
    )


btn_cols = st.columns(2)
if btn_cols[0].button("📄 Generate DOCX", type="primary", use_container_width=True):
    out = Path(tempfile.mkdtemp(prefix="hsingmd_docx_")) / f"{job_name}.docx"
    generate_docx(_build_report_data(), out)
    btn_cols[0].download_button("⬇ Download DOCX", out.read_bytes(),
                                 file_name=out.name, type="primary")

if btn_cols[1].button("📊 Generate PPTX", type="primary", use_container_width=True):
    out = Path(tempfile.mkdtemp(prefix="hsingmd_pptx_")) / f"{job_name}.pptx"
    generate_pptx(_build_report_data(), out)
    btn_cols[1].download_button("⬇ Download PPTX", out.read_bytes(),
                                 file_name=out.name, type="primary")
