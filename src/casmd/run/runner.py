"""Drive the bundled GROMACS pipeline (run_md.sh) against a bundle dir.

This is what `casmd-run` calls. It:
  1. Optionally rewrites step4_production.mdp's nsteps for the user-picked length.
  2. Spawns run_md.sh, streams stdout line-by-line.
  3. Parses each line through casmd.run.progress for on_progress callbacks.
  4. Returns a RunResult with exit code + wall time + log path.
"""
from __future__ import annotations
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from casmd.run.progress import ProgressEvent, parse_progress_line


_DEFAULT_TIMESTEP_FS = 2.0  # 2 fs is the CasMD default


@dataclass(frozen=True)
class RunResult:
    """Outcome of run_md_locally()."""
    exit_code: int
    production_ns: float
    wall_time_seconds: float
    log_path: Path
    analysis_dir: Path | None


def _rewrite_production_nsteps(mdp_path: Path, production_ns: float,
                               timestep_fs: float = _DEFAULT_TIMESTEP_FS) -> None:
    """Edit step4_production.mdp in-place to match the requested ns.

    nsteps = production_ns * 1000 / timestep_ps  (timestep_ps = timestep_fs / 1000)
           = production_ns * 1_000_000 / timestep_fs
    """
    if not mdp_path.exists():
        return
    new_nsteps = int(production_ns * 1_000_000 / timestep_fs)
    text = mdp_path.read_text()
    new_text = re.sub(
        r"^(nsteps\s*=\s*)\d+",
        rf"\g<1>{new_nsteps}",
        text,
        flags=re.MULTILINE,
    )
    mdp_path.write_text(new_text)


def run_md_locally(
    *,
    bundle_dir: Path,
    production_ns: float = 50.0,
    on_progress: Optional[Callable[[ProgressEvent], None]] = None,
    timestep_fs: float = _DEFAULT_TIMESTEP_FS,
) -> RunResult:
    """Run the bundle's run_md.sh and stream progress events.

    Args:
        bundle_dir: directory containing run_md.sh + system.{gro,top} + MDPs.
        production_ns: how long to run production for (overrides MDP default).
        on_progress: optional callback invoked for each ProgressEvent.
        timestep_fs: MDP timestep in fs (must match the bundle's MDP).

    Returns: RunResult.

    Raises FileNotFoundError if run_md.sh is missing.
    """
    bundle_dir = Path(bundle_dir).resolve()
    run_sh = bundle_dir / "run_md.sh"
    if not run_sh.exists():
        raise FileNotFoundError(
            f"run_md.sh not found in {bundle_dir}. Pass the directory you "
            f"unzipped from CasMD's Stage 1 build."
        )

    # Override the production length if the user picked a non-default ns.
    _rewrite_production_nsteps(
        bundle_dir / "step4_production.mdp",
        production_ns=production_ns, timestep_fs=timestep_fs,
    )

    log_path = bundle_dir / "md.log"
    start = time.monotonic()
    proc = subprocess.Popen(
        ["bash", str(run_sh)],
        cwd=str(bundle_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if proc.stdout is not None:
        for line in proc.stdout:
            evt = parse_progress_line(line)
            if evt is not None and on_progress is not None:
                on_progress(evt)

    exit_code = proc.wait()
    elapsed = time.monotonic() - start

    analysis_dir = bundle_dir / "analysis"
    return RunResult(
        exit_code=exit_code,
        production_ns=production_ns,
        wall_time_seconds=elapsed,
        log_path=log_path,
        analysis_dir=analysis_dir if analysis_dir.exists() else None,
    )
