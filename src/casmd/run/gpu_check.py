"""Detect available GPU acceleration for local MD runs.

Returns a `GpuInfo` with a realistic ns/day estimate so the Streamlit UI can
warn the user before they kick off a multi-day run on a CPU-only laptop.
"""
from __future__ import annotations
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GpuInfo:
    """Result of a GPU pre-flight scan.

    kind: 'nvidia' | 'apple' | 'cpu'
    name: human-readable device name (e.g. "NVIDIA RTX 4090")
    vram_gb: 0 for non-CUDA paths
    est_ns_per_day: realistic 50k-atom tri-complex throughput
    recommendation: one-sentence guidance for the user
    """
    kind: str
    name: str
    vram_gb: int
    est_ns_per_day: float
    recommendation: str


def _run_nvidia_smi() -> Optional[str]:
    """Returns the first line of nvidia-smi --query-gpu output or None."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader"],
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode().strip()
        return out.splitlines()[0] if out else None
    except (FileNotFoundError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired):
        return None


# Empirical estimates for a ~50k-atom protein-NA tri-complex.
# These are conservative; real numbers depend on system size + clock speeds.
_NVIDIA_ESTIMATES = [
    (re.compile(r"4090|H100|H200|A100"), 80.0),
    (re.compile(r"4080|A6000|L40"),       60.0),
    (re.compile(r"3090|L20|4070"),         40.0),
    (re.compile(r"3080|4060|2080"),        30.0),
    (re.compile(r"3070|3060|T4"),          22.0),
    (re.compile(r"RTX|Tesla|Quadro"),      18.0),
]


def _nvidia_ns_per_day(name: str) -> float:
    for pat, rate in _NVIDIA_ESTIMATES:
        if pat.search(name):
            return rate
    return 15.0  # generic NVIDIA fallback


def detect_gpu() -> GpuInfo:
    """Best-effort GPU detection for the local-MD pre-flight check."""
    # 1. NVIDIA via nvidia-smi
    smi = _run_nvidia_smi()
    if smi:
        # Format: "NVIDIA GeForce RTX 4090, 24564 MiB"
        name, _, mem_str = smi.partition(",")
        name = name.strip()
        vram_gb = int(int(re.sub(r"\D", "", mem_str) or 0) / 1024) if mem_str else 0
        ns = _nvidia_ns_per_day(name)
        return GpuInfo(
            kind="nvidia", name=name, vram_gb=vram_gb,
            est_ns_per_day=ns,
            recommendation="Pass `--gpu cuda` to use this GPU for full GROMACS speed.",
        )

    # 2. Apple Silicon (no Metal acceleration for GROMACS → CPU-only)
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return GpuInfo(
            kind="apple", name="Apple Silicon (CPU-only, no Metal in GROMACS)",
            vram_gb=0,
            est_ns_per_day=8.0,
            recommendation=(
                "GROMACS has no Metal backend yet; runs CPU-only on M-series. "
                "For runs >50 ns, use an HPC cluster or a Linux GPU workstation."
            ),
        )

    # 3. Plain CPU fallback — scale with core count. GROMACS on a ~50-100k-atom
    # tri-complex does very roughly ~0.5 ns/day per modern core, with
    # diminishing returns past ~16 cores. On a 2-vCPU host (e.g. a free HF
    # Space) that's ~1 ns/day — i.e. ~50 days for a 50 ns run.
    cores = os.cpu_count() or 2
    est = round(0.5 * min(cores, 16), 1)
    return GpuInfo(
        kind="cpu", name=f"{platform.machine()} CPU ({cores} cores)",
        vram_gb=0,
        est_ns_per_day=est,
        recommendation=(
            f"No GPU detected — GROMACS runs CPU-only (~{est:g} ns/day on "
            f"{cores} cores). Fine for a short look; use a GPU or the HPC "
            f"bundle for anything beyond a few ns."
        ),
    )


def format_eta(hours: float) -> str:
    """Human-friendly wall-time estimate."""
    if hours < 24:
        return f"~{int(round(hours))} hours"
    days = hours / 24
    return f"~{days:.1f} days"
