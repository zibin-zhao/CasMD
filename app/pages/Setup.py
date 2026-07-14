"""First-run Setup — shows detected hardware + the active GROMACS build."""
import os
import platform
import streamlit as st

from casmd.run.gpu_check import detect_gpu
from casmd.desktop.env_select import choose_env_name

st.title("Welcome to StrandMD Desktop")

gpu = detect_gpu()
system = platform.system()

# The launcher resolves the actual GROMACS build (including a CUDA→CPU driver
# fallback probe) and passes the result down via env vars. Prefer that; fall
# back to the dir-only choose_env_name logic when running outside the launcher
# (e.g. dev / `streamlit run`).
launcher_accel = os.environ.get("CASMD_GMX_ACCEL")
if launcher_accel:
    accel_kind = launcher_accel
    fell_back = os.environ.get("CASMD_GMX_FELL_BACK") == "1"
else:
    accel_kind = "cuda" if choose_env_name(gpu.kind, system) == "gmx_cuda" else "cpu"
    fell_back = False

env = "gmx_cuda" if accel_kind == "cuda" else "gmx_cpu"
accel = "GPU-accelerated" if accel_kind == "cuda" else "CPU"

st.subheader("Your computer")
c1, c2 = st.columns(2)
c1.metric("Operating system", system or "unknown")
c2.metric("Compute device", gpu.name)

if fell_back:
    st.warning("⚠️ NVIDIA GPU detected but its driver couldn't load the CUDA "
               "build — running on **CPU**.")
elif env == "gmx_cuda":
    st.success(f"✓ {gpu.name} detected → **{accel} GROMACS** is active. "
               "Runs will use your GPU.")
elif system == "Darwin":
    st.info("✓ macOS → **CPU GROMACS** (GROMACS has no GPU acceleration on Mac). "
            "Fine for small systems; use an HPC cluster for long runs.")
else:
    st.info("✓ **CPU GROMACS** active (no NVIDIA GPU detected). "
            "Fine for short runs; a GPU makes production runs much faster.")

st.caption("Everything is installed — no Docker, no terminal, no GROMACS download needed.")

if st.button("Start — build a system →", type="primary", width="stretch"):
    st.session_state["privacy_acked"] = True
    st.switch_page("pages/1_Stage_1_Predict_and_Bundle.py")
