"""Compare two GROMACS systems on key invariants: atom count, box, ions."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

import MDAnalysis as mda


@dataclass(frozen=True)
class TopologyStats:
    n_atoms: int
    n_water_residues: int
    n_na: int
    n_cl: int
    box_volume_nm3: float
    box_dims_nm: tuple[float, float, float]


@dataclass(frozen=True)
class ComparisonReport:
    atom_count_delta: int
    box_volume_relative_delta: float  # (new - ref) / ref
    na_delta: int
    cl_delta: int

    def within_tolerance(
        self, *, atom_pct: float = 1.0, box_pct: float = 5.0, ion_count: int = 2
    ) -> bool:
        return (
            abs(self.atom_count_delta) <= max(1, int(0.01 * atom_pct)) * 1
            and abs(self.box_volume_relative_delta) <= box_pct / 100.0
            and abs(self.na_delta) <= ion_count
            and abs(self.cl_delta) <= ion_count
        )


def summarize_gromacs_system(gro_path: Path) -> TopologyStats:
    u = mda.Universe(str(gro_path))
    n_atoms = u.atoms.n_atoms
    waters = u.select_atoms(
        "resname HOH or resname WAT or resname SOL or resname TIP3 or resname TP3"
    )
    n_water_res = len(set(waters.resids))
    n_na = len(u.select_atoms("resname NA or resname Na+ or resname SOD"))
    n_cl = len(u.select_atoms("resname CL or resname Cl- or resname CLA"))
    dims = u.dimensions[:3] / 10.0  # Å → nm
    vol = float(dims[0] * dims[1] * dims[2])
    return TopologyStats(
        n_atoms=n_atoms,
        n_water_residues=n_water_res,
        n_na=n_na,
        n_cl=n_cl,
        box_volume_nm3=vol,
        box_dims_nm=(float(dims[0]), float(dims[1]), float(dims[2])),
    )


def compare_systems(ref: TopologyStats, new: TopologyStats) -> ComparisonReport:
    return ComparisonReport(
        atom_count_delta=new.n_atoms - ref.n_atoms,
        box_volume_relative_delta=(new.box_volume_nm3 - ref.box_volume_nm3) / ref.box_volume_nm3,
        na_delta=new.n_na - ref.n_na,
        cl_delta=new.n_cl - ref.n_cl,
    )
