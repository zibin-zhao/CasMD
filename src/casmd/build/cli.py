"""`casmd-build` CLI — build a GROMACS-ready system from a PDB."""
from __future__ import annotations
import argparse
from pathlib import Path

from casmd.build.system import build_system
from casmd.build.tleap_recipe import BuildConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a GROMACS-ready system from a PDB.")
    parser.add_argument("pdb", type=Path, help="Input PDB (protein/RNA/DNA chains)")
    parser.add_argument("output_dir", type=Path, help="Output directory")
    parser.add_argument("--prefix", default="system", help="Output file prefix")
    parser.add_argument("--box-padding", type=float, default=12.0, help="Box padding in Å")
    args = parser.parse_args()

    config = BuildConfig(box_padding_A=args.box_padding)
    bundle = build_system(args.pdb, args.output_dir, config, prefix=args.prefix)
    print(f"Wrote:\n  {bundle.top}\n  {bundle.gro}\n  {bundle.solvated_pdb}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
