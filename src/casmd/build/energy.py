"""Compute single-point potential energy via GROMACS mdrun -rerun."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil as _sh
import subprocess


@dataclass(frozen=True)
class EnergyResult:
    potential_kJ_mol: float


_MDP = """\
integrator               = md
nsteps                   = 0
nstenergy                = 1
cutoff-scheme            = Verlet
coulombtype              = PME
rcoulomb                 = 1.0
vdwtype                  = Cut-off
rvdw                     = 1.0
DispCorr                 = EnerPres
pbc                      = xyz
constraints              = none
"""

_MIN_MDP = """\
integrator               = steep
nsteps                   = 1000
emtol                    = 1000.0
emstep                   = 0.01
cutoff-scheme            = Verlet
coulombtype              = PME
rcoulomb                 = 1.0
vdwtype                  = Cut-off
rvdw                     = 1.0
DispCorr                 = EnerPres
pbc                      = xyz
constraints              = none
"""


def _stage_files(top: Path, gro: Path, work_dir: Path) -> tuple[Path, Path]:
    """Copy top, gro, and toppar/ into work_dir so #include paths resolve."""
    top = Path(top)
    gro = Path(gro)
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    toppar = top.parent / "toppar"
    if toppar.exists():
        dest_toppar = work_dir / "toppar"
        if dest_toppar.exists():
            _sh.rmtree(dest_toppar)
        _sh.copytree(toppar, dest_toppar)

    local_top = work_dir / "input.top"
    local_gro = work_dir / "input.gro"
    _sh.copy(top, local_top)
    _sh.copy(gro, local_gro)
    return local_top, local_gro


def _extract_potential(stdout: str) -> float:
    """Parse 'Potential  <value>' from gmx energy stdout."""
    for line in stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == "Potential" and len(parts) >= 2:
            return float(parts[1])
    raise RuntimeError(f"could not parse potential energy from gmx energy:\n{stdout}")


def single_point_energy(top: Path, gro: Path, work_dir: Path) -> EnergyResult:
    gmx = _sh.which("gmx")
    if gmx is None:
        raise RuntimeError("gmx not on PATH. Activate casmd conda env.")
    work_dir = Path(work_dir)

    local_top, local_gro = _stage_files(top, gro, work_dir)

    mdp = work_dir / "sp.mdp"
    mdp.write_text(_MDP)

    tpr = work_dir / "sp.tpr"
    subprocess.run(
        [gmx, "grompp", "-f", str(mdp), "-c", str(local_gro), "-p", str(local_top),
         "-o", str(tpr), "-maxwarn", "5"],
        cwd=work_dir, check=True, capture_output=True, text=True,
    )
    subprocess.run(
        [gmx, "mdrun", "-s", str(tpr), "-rerun", str(local_gro), "-deffnm", "sp"],
        cwd=work_dir, check=True, capture_output=True, text=True,
    )
    proc = subprocess.run(
        [gmx, "energy", "-f", "sp.edr", "-o", "sp.xvg"],
        input="Potential\n", cwd=work_dir, capture_output=True, text=True, check=True,
    )
    pot = _extract_potential(proc.stdout)
    return EnergyResult(potential_kJ_mol=pot)


def minimize_then_energy(top: Path, gro: Path, work_dir: Path) -> EnergyResult:
    """Steepest-descent minimization (1000 steps cap, emtol 1000) then potential energy."""
    gmx = _sh.which("gmx")
    if gmx is None:
        raise RuntimeError("gmx not on PATH.")
    work_dir = Path(work_dir)

    local_top, local_gro = _stage_files(top, gro, work_dir)

    mdp = work_dir / "min.mdp"
    mdp.write_text(_MIN_MDP)

    subprocess.run(
        [gmx, "grompp", "-f", str(mdp), "-c", str(local_gro), "-p", str(local_top),
         "-o", "min.tpr", "-maxwarn", "5"],
        cwd=work_dir, check=True, capture_output=True, text=True,
    )
    subprocess.run(
        [gmx, "mdrun", "-deffnm", "min"],
        cwd=work_dir, check=True, capture_output=True, text=True,
    )
    proc = subprocess.run(
        [gmx, "energy", "-f", "min.edr", "-o", "min.xvg"],
        input="Potential\n", cwd=work_dir, capture_output=True, text=True, check=True,
    )
    pot = _extract_potential(proc.stdout)
    return EnergyResult(potential_kJ_mol=pot)
