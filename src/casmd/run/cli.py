"""`casmd-run <bundle_dir> [--ns N]` — drive the bundle's MD pipeline locally."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from casmd.run.gpu_check import detect_gpu, format_eta
from casmd.run.runner import run_md_locally


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="casmd-run",
        description="Run a CasMD bundle's MD pipeline locally (em → NVT → NPT → production → analyze).",
    )
    p.add_argument("bundle_dir", type=Path,
                   help="Path to the unzipped CasMD bundle directory.")
    p.add_argument("--ns", type=float, default=50.0,
                   help="Production length in nanoseconds (default: 50).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    gpu = detect_gpu()
    eta_hours = args.ns * 24 / max(gpu.est_ns_per_day, 0.1)
    print(f"Hardware:   {gpu.kind} — {gpu.name}")
    print(f"Estimate:   {gpu.est_ns_per_day:.0f} ns/day")
    print(f"Target run: {args.ns:g} ns → {format_eta(eta_hours)}")
    print(f"Bundle:     {args.bundle_dir.resolve()}")
    if gpu.kind != "nvidia":
        print(f"\n⚠ {gpu.recommendation}\n")

    def _print(evt) -> None:
        if evt.current_step is not None:
            print(f"  step {evt.current_step:>12,}  t={evt.current_time_ps:8.1f} ps", flush=True)
        if evt.ns_per_day is not None:
            print(f"  Performance: {evt.ns_per_day:.2f} ns/day", flush=True)

    result = run_md_locally(
        bundle_dir=args.bundle_dir,
        production_ns=args.ns,
        on_progress=_print,
    )
    print(f"\nDone in {result.wall_time_seconds:.0f} s. exit={result.exit_code}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
