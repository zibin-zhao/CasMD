"""Measure this machine's real MD throughput with a short GROMACS run.

Runs a brief energy minimization of the *built* system — crash-safe on an
unequilibrated structure, unlike a production run — times it, and converts the
measured steps/sec into an approximate MD ns/day. This lets the Stage-1 Build
step report a measured run-time estimate for the user's specific system rather
than the size-agnostic default in `gpu_check`.

Approximate by design: an EM force evaluation is close to (but a little cheaper
than) a full MD step, so a conservative overhead factor is applied so we never
over-promise speed.
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

# An MD step does a bit more than an EM step (constraints, T/P coupling), so
# scale the EM-derived throughput down to avoid over-estimating speed.
_MD_OVERHEAD_FACTOR = 0.85

# Matches GROMACS EM summary lines like:
#   "Steepest Descents converged to Fmax < 100 in 164 steps"
#   "Steepest Descents did not converge to Fmax < 10 in 201 steps"
_STEPS_RE = re.compile(r"in\s+(\d+)\s+steps", re.IGNORECASE)


@dataclass(frozen=True)
class BenchResult:
    """Outcome of a CPU/GPU speed benchmark."""
    ns_per_day: float      # approximate MD throughput on this hardware
    steps: int             # EM steps actually run
    wall_seconds: float    # wall time of the mdrun call
    n_atoms: int


def gmx_available(gmx: str = "gmx") -> bool:
    """True if the GROMACS binary is on PATH (present on the Space image)."""
    return shutil.which(gmx) is not None


def count_atoms_gro(gro_path) -> int:
    """The second line of a GROMACS .gro file is the atom count."""
    with open(gro_path) as fh:
        fh.readline()                      # title line
        return int(fh.readline().strip())


def parse_em_steps(log_text: str, default: int = 0) -> int:
    """Number of EM steps completed, parsed from a GROMACS md.log."""
    m = _STEPS_RE.search(log_text)
    return int(m.group(1)) if m else default


def ns_per_day_from_steps(steps: int, wall_seconds: float,
                          timestep_fs: float = 2.0) -> float:
    """Convert measured EM steps/sec into an approximate MD ns/day."""
    if steps <= 0 or wall_seconds <= 0:
        return 0.0
    steps_per_sec = steps / wall_seconds
    ns_per_day = steps_per_sec * 86400.0 * timestep_fs * 1e-6
    return round(ns_per_day * _MD_OVERHEAD_FACTOR, 2)


def run_cpu_benchmark(bundle_dir, *, gmx: str = "gmx", em_nsteps: int = 200,
                      timeout_s: int = 75, ntomp: int | None = None,
                      timestep_fs: float = 2.0) -> BenchResult:
    """Grompp + a short EM on the built system; return measured throughput.

    Reuses the bundle's own `step1_minimization.mdp` (so the settings match the
    real run) and caps the workload with `mdrun -nsteps`, which overrides the
    tpr. Raises RuntimeError if GROMACS is missing or grompp/mdrun fails.
    """
    bundle_dir = Path(bundle_dir)
    gro = bundle_dir / "system.gro"
    top = bundle_dir / "system.top"
    mdp = bundle_dir / "step1_minimization.mdp"
    for f in (gro, top, mdp):
        if not f.exists():
            raise RuntimeError(f"bundle is missing {f.name}")
    if not gmx_available(gmx):
        raise RuntimeError("GROMACS (gmx) not found on PATH")

    n_atoms = count_atoms_gro(gro)
    if ntomp is None:
        # Leave one core for the shared Streamlit process on the public Space.
        ntomp = max(1, (os.cpu_count() or 2) - 1)
    log_path = bundle_dir / "bench_em.log"

    # grompp (fast preprocessor; still guard its timeout so a hang can't hold
    # the app). Timed so mdrun below shares one wall-clock budget with it.
    t_start = time.monotonic()
    try:
        grompp = subprocess.run(
            [gmx, "grompp", "-f", "step1_minimization.mdp", "-o", "bench_em.tpr",
             "-c", "system.gro", "-r", "system.gro", "-p", "system.top",
             "-maxwarn", "99"],
            cwd=bundle_dir, capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("grompp timed out")
    if grompp.returncode != 0:
        raise RuntimeError(f"grompp failed: {grompp.stderr.strip()[-400:]}")

    # Single shared budget: mdrun gets whatever time is left, so total blocking
    # is bounded by timeout_s (not 2x).
    md_budget = max(5.0, timeout_s - (time.monotonic() - t_start))
    t0 = time.monotonic()
    try:
        mdrun = subprocess.run(
            [gmx, "mdrun", "-deffnm", "bench_em", "-nsteps", str(em_nsteps),
             "-ntomp", str(ntomp)],
            cwd=bundle_dir, capture_output=True, text=True, timeout=md_budget,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "benchmark timed out — this system is too large to measure quickly here"
        )
    wall = time.monotonic() - t0
    if mdrun.returncode != 0:
        raise RuntimeError(f"mdrun failed: {mdrun.stderr.strip()[-400:]}")

    # No fabrication: if the real step count can't be read, degrade to the
    # estimate rather than assuming the full cap ran.
    steps = parse_em_steps(log_path.read_text() if log_path.exists() else "")
    if steps <= 0:
        raise RuntimeError("could not read the step count from the GROMACS log")
    return BenchResult(ns_per_day_from_steps(steps, wall, timestep_fs),
                       steps, wall, n_atoms)
