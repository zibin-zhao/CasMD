"""Invoke AmberTools tleap as a subprocess."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path


class TleapNotFoundError(RuntimeError):
    """Raised when the `tleap` binary cannot be located on PATH."""


class TleapFailedError(RuntimeError):
    """Raised when tleap exits non-zero or its expected output files are missing."""


def run_tleap(
    recipe: str,
    work_dir: Path,
    *,
    output_prefix: str,
    timeout_sec: int = 600,
) -> tuple[Path, Path]:
    """Run tleap with `recipe` as stdin. Return (prmtop_path, inpcrd_path).

    `work_dir` is the cwd for tleap; outputs are written there.
    """
    tleap = shutil.which("tleap")
    if tleap is None:
        raise TleapNotFoundError(
            "tleap not found on PATH. Activate the casmd conda environment "
            "(`conda activate gmxMMPBSA`)."
        )
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = work_dir / f"{output_prefix}.in"
    recipe_path.write_text(recipe)

    result = subprocess.run(
        [tleap, "-f", recipe_path.name],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )

    prmtop = work_dir / f"{output_prefix}.prmtop"
    inpcrd = work_dir / f"{output_prefix}.inpcrd"

    if result.returncode != 0 or not prmtop.exists() or not inpcrd.exists():
        log = (work_dir / "leap.log").read_text() if (work_dir / "leap.log").exists() else ""
        raise TleapFailedError(
            f"tleap failed (rc={result.returncode}).\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}\nleap.log tail:\n{log[-2000:]}"
        )
    return prmtop, inpcrd
