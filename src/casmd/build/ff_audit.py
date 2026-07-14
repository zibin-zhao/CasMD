"""Audit a GROMACS topology for residue composition (proxy for FF assignment)."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os

import parmed as pmd

from casmd.build.chains import PROTEIN_RESIDUES, RNA_RESIDUES, DNA_RESIDUES


@dataclass(frozen=True)
class ForceFieldAudit:
    n_protein_residues: int
    n_rna_residues: int
    n_dna_residues: int
    n_water_residues: int
    n_ion_residues: int
    unknown_residues: tuple[str, ...]


_ION_RESIDUES = {"NA", "CL", "Na+", "Cl-", "SOD", "CLA", "K", "MG"}
_WATER_RESIDUES = {"HOH", "WAT", "SOL", "TIP3", "TP3", "T3P"}


def audit_topology(top_path: Path) -> ForceFieldAudit:
    """Load a GROMACS topology and count residues by type.

    Handles #include directives by temporarily changing to the topology's
    parent directory during parsing.
    """
    top_path = Path(top_path)
    orig_cwd = os.getcwd()
    try:
        os.chdir(top_path.parent)
        structure = pmd.load_file(top_path.name)
    finally:
        os.chdir(orig_cwd)

    protein = rna = dna = water = ion = 0
    unknown: list[str] = []
    for r in structure.residues:
        name = r.name.strip()
        if name in PROTEIN_RESIDUES:
            protein += 1
        elif name in RNA_RESIDUES:
            rna += 1
        elif name in DNA_RESIDUES:
            dna += 1
        elif name in _WATER_RESIDUES:
            water += 1
        elif name in _ION_RESIDUES:
            ion += 1
        else:
            unknown.append(name)

    return ForceFieldAudit(
        n_protein_residues=protein,
        n_rna_residues=rna,
        n_dna_residues=dna,
        n_water_residues=water,
        n_ion_residues=ion,
        unknown_residues=tuple(sorted(set(unknown))),
    )
