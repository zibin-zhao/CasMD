"""Count explicit water molecules in a solvated PDB.

Counts oxygen atoms belonging to a water residue (WAT / HOH / SOL / TIP3).
Counting the oxygen atom alone is the most robust way to count molecules
regardless of how many hydrogens are written per water.
"""
from __future__ import annotations
from pathlib import Path


_WATER_RESNAMES = {"WAT", "HOH", "SOL", "TIP3", "T3P"}


def count_waters(pdb_path: Path) -> int:
    """Return the number of water molecules in a PDB file.

    Counts oxygen atoms (atom name starting with 'O') belonging to a water
    residue. One oxygen == one water molecule.
    """
    pdb_path = Path(pdb_path)
    n = 0
    for line in pdb_path.read_text().splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        # PDB fixed columns: atom name 13-16, residue name 18-20.
        atom_name = line[12:16].strip()
        res_name = line[17:20].strip()
        if res_name in _WATER_RESNAMES and atom_name.startswith("O"):
            n += 1
    return n
