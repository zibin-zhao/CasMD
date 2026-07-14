"""`casmd-bundle` CLI: produce a single zip ready for HPC submission."""
from __future__ import annotations
import argparse
from pathlib import Path

from casmd.bundle.packager import package_bundle
from casmd.bundle.spec import BundleSpec


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="casmd-bundle",
                                description="Package a built GROMACS system into an HPC-ready zip.")
    p.add_argument("system_dir", type=Path, help="Directory from `casmd-build` (system.top/.gro live here)")
    p.add_argument("-o", "--output", type=Path, required=True, help="Output zip path")
    p.add_argument("--name", default="casmd_run", help="Job name (top-level dir inside the zip)")
    p.add_argument("--production-ns", type=float, default=500.0, help="Production length in ns")
    p.add_argument("--nvt-ps", type=float, default=500.0)
    p.add_argument("--npt-ps", type=float, default=500.0)
    p.add_argument("--temp", type=float, default=310.15, help="Temperature in K")
    p.add_argument("--account", default="hsinglab")
    p.add_argument("--partition", default="gpu-l20")
    p.add_argument("--gpus-per-node", default="l20:4")
    p.add_argument("--cpus-per-task", type=int, default=64)
    p.add_argument("--time-hours", type=int, default=72)
    p.add_argument("--email")
    p.add_argument("--gmx", default="gmx_mpi", help="GROMACS binary name")
    p.add_argument("--no-spack", action="store_true", help="Do not emit `spack env activate` in submit.sh")
    args = p.parse_args(argv)

    spec = BundleSpec(
        production_ns=args.production_ns,
        nvt_ps=args.nvt_ps,
        npt_ps=args.npt_ps,
        temperature_K=args.temp,
        job_name=args.name,
        account=args.account,
        partition=args.partition,
        gpus_per_node=args.gpus_per_node,
        cpus_per_task=args.cpus_per_task,
        time_hours=args.time_hours,
        email=args.email,
        gmx_binary=args.gmx,
        spack_env=None if args.no_spack else "gromacs",
    )
    out = package_bundle(args.system_dir, spec, args.output)
    print(f"Wrote bundle: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
