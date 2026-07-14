"""Configuration object for an CasMD HPC bundle.

The simulation defaults use ff19SB-compatible MDPs, 310.15 K, and a 500 ns
production target. Cluster settings remain editable for each deployment.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class BundleSpec:
    # ---- MDP-side ----
    production_ns: float = 500.0
    nvt_ps: float = 500.0
    npt_ps: float = 500.0
    timestep_fs: float = 2.0
    temperature_K: float = 310.15
    output_every_ps: float = 100.0
    em_steps: int = 50_000

    # ---- SLURM-side (editable example cluster defaults) ----
    job_name: str = "casmd_run"
    account: str = "hsinglab"
    partition: str = "gpu-l20"
    gpus_per_node: str = "l20:4"
    cpus_per_task: int = 64
    nodes: int = 1
    time_hours: int = 72
    email: str | None = None

    # ---- GROMACS-side ----
    gmx_binary: str = "gmx_mpi"
    spack_env: str | None = "gromacs"

    # ---- Derived ----
    @property
    def production_steps(self) -> int:
        return int(self.production_ns * 1_000 / (self.timestep_fs / 1_000.0))

    @property
    def nvt_steps(self) -> int:
        return int(self.nvt_ps / (self.timestep_fs / 1_000.0))

    @property
    def npt_steps(self) -> int:
        return int(self.npt_ps / (self.timestep_fs / 1_000.0))

    @property
    def output_every_steps(self) -> int:
        return int(self.output_every_ps / (self.timestep_fs / 1_000.0))
