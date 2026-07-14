"""Detect whether each chain in a PDB is protein, RNA, or DNA."""
from __future__ import annotations
from enum import Enum
from pathlib import Path

import MDAnalysis as mda

PROTEIN_RESIDUES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
    # protonation variants
    "HID", "HIE", "HIP", "CYX", "CYM", "LYN", "ASH", "GLH",
}
RNA_RESIDUES = {"A", "U", "G", "C", "RA", "RU", "RG", "RC", "A3", "U3", "G3", "C3", "A5", "U5", "G5", "C5"}
DNA_RESIDUES = {"DA", "DT", "DG", "DC", "DA3", "DT3", "DG3", "DC3", "DA5", "DT5", "DG5", "DC5"}


class ChainKind(str, Enum):
    PROTEIN = "protein"
    RNA = "rna"
    DNA = "dna"
    UNKNOWN = "unknown"


def detect_chains(pdb_path: Path) -> dict[str, ChainKind]:
    """Return {chain_id: kind} for every chain in the PDB."""
    pdb_path = Path(pdb_path)
    if not pdb_path.exists():
        raise FileNotFoundError(pdb_path)

    u = mda.Universe(str(pdb_path))
    out: dict[str, ChainKind] = {}
    for seg in u.segments:
        # MDAnalysis uses segid; PDB chainID typically maps to it
        resnames = {r.resname.strip() for r in seg.residues}
        kind = _classify(resnames)
        chain_id = seg.segid if seg.segid else "A"
        out[chain_id] = kind
    return out


def _classify(resnames: set[str]) -> ChainKind:
    if resnames & PROTEIN_RESIDUES:
        return ChainKind.PROTEIN
    if resnames & RNA_RESIDUES:
        return ChainKind.RNA
    if resnames & DNA_RESIDUES:
        return ChainKind.DNA
    return ChainKind.UNKNOWN
