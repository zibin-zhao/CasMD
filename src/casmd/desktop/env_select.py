"""Pick the right bundled GROMACS environment for the detected hardware.

The installer creates two GROMACS conda envs under the install prefix
(`envs/gmx_cuda` on Windows/Linux; `envs/gmx_cpu` everywhere). This module
decides which to activate at launch and lists the directories to prepend to
PATH so `gmx` and its runtime libraries resolve.
"""
from __future__ import annotations
import subprocess
from dataclasses import dataclass
from pathlib import Path

CUDA_ENV = "gmx_cuda"
CPU_ENV = "gmx_cpu"


@dataclass(frozen=True)
class GmxSelection:
    env_name: str                 # "gmx_cuda" | "gmx_cpu"
    env_prefix: Path              # <install_prefix>/envs/<env_name>
    bin_dirs: tuple[Path, ...]    # dirs to prepend to PATH
    accel: str                    # "cuda" | "cpu"
    fell_back: bool = False       # True if CUDA was requested but we dropped to CPU


def choose_env_name(gpu_kind: str, system: str) -> str:
    """CUDA only on NVIDIA + Windows/Linux; CPU everywhere else (incl. macOS)."""
    if gpu_kind == "nvidia" and system in ("Windows", "Linux"):
        return CUDA_ENV
    return CPU_ENV


def env_bin_dirs(env_prefix: Path, system: str) -> tuple[Path, ...]:
    """Directories to prepend to PATH (conda env layout differs by OS)."""
    if system == "Windows":
        return (
            env_prefix,
            env_prefix / "Library" / "bin",
            env_prefix / "Library" / "mingw-w64" / "bin",
            env_prefix / "Scripts",
        )
    return (env_prefix / "bin",)


def gmx_exe(env_prefix: Path, system: str) -> Path:
    """Path to the `gmx` binary inside a conda env (layout differs by OS)."""
    if system == "Windows":
        return env_prefix / "Library" / "bin" / "gmx.exe"
    return env_prefix / "bin" / "gmx"


def probe_gmx_ok(env_prefix: Path, system: str, run=None) -> bool:
    """Return True iff `gmx --version` exits 0 for the env's binary.

    Catches a CUDA build that cannot load a broken/old NVIDIA driver at runtime.
    Any exception (missing binary, timeout, etc.) counts as a failed probe.
    """
    if run is None:
        run = subprocess.run
    try:
        result = run(
            [str(gmx_exe(env_prefix, system)), "--version"],
            timeout=20, capture_output=True,
        )
    except Exception:
        return False
    return result.returncode == 0


def select_gmx(*, gpu_kind: str, system: str, install_prefix: Path,
               env_exists=None, probe=None) -> GmxSelection:
    """Resolve the GROMACS env, falling back to CPU if the CUDA env is absent
    (e.g. NVIDIA GPU on a machine whose driver is missing, or a CPU-only build).

    If `probe` is provided, the CUDA build is also functionally checked
    (`gmx --version`); a failing probe forces a CPU fallback even when the env
    directory exists. `probe` defaults to None, preserving dir-only behavior."""
    if env_exists is None:
        env_exists = lambda p: p.exists()
    name = choose_env_name(gpu_kind, system)
    prefix = install_prefix / "envs" / name
    fell_back = False
    if name == CUDA_ENV and (
        not env_exists(prefix)
        or (probe is not None and not probe(prefix, system))
    ):
        fell_back = True
        name = CPU_ENV
        prefix = install_prefix / "envs" / name
    accel = "cuda" if name == CUDA_ENV else "cpu"
    return GmxSelection(env_name=name, env_prefix=prefix,
                        bin_dirs=env_bin_dirs(prefix, system), accel=accel,
                        fell_back=fell_back)
