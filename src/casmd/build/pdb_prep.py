"""Run AmberTools pdb4amber to clean a PDB for tleap consumption.

This strips 5'-terminal phosphates from nucleic-acid chains, removes
non-standard atoms, drops ions/waters, and renumbers chains to match
tleap's residue library.
"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path

_NUCLEIC_RESNAMES = {"DA", "DT", "DG", "DC", "A", "U", "G", "C"}
# Atoms that tleap's DA5/DG5/U5/etc. templates do NOT define types for
_5PRIME_PHOSPHATE_ATOMS = {"P", "OP1", "OP2", "OP3"}


class Pdb4AmberNotFoundError(RuntimeError):
    pass


class Pdb4AmberFailedError(RuntimeError):
    pass


def _strip_5prime_phosphates(pdb_text: str) -> str:
    """Remove P/OP1/OP2/OP3 from the first residue of each nucleic-acid chain.

    tleap's 5'-capped templates (DA5, DG5, U5, …) do not carry those atoms;
    passing them in causes 'Atom does not have a type' FATAL errors at
    saveAmberParm time.
    """
    lines = pdb_text.splitlines(keepends=True)
    # Pass 1: find (chain, resseq) of the first nucleic residue per chain
    first_nuc: dict[str, int] = {}
    for line in lines:
        if not line.startswith("ATOM"):
            continue
        chain = line[21]
        resname = line[17:20].strip()
        resseq = int(line[22:26])
        if resname in _NUCLEIC_RESNAMES and chain not in first_nuc:
            first_nuc[chain] = resseq

    # Pass 2: drop P/OP1/OP2/OP3 lines that belong to a first-nucleic residue
    out: list[str] = []
    for line in lines:
        if line.startswith("ATOM"):
            chain = line[21]
            resname = line[17:20].strip()
            atomname = line[12:16].strip()
            resseq = int(line[22:26])
            if (
                chain in first_nuc
                and resseq == first_nuc[chain]
                and resname in _NUCLEIC_RESNAMES
                and atomname in _5PRIME_PHOSPHATE_ATOMS
            ):
                continue  # drop this atom
        out.append(line)
    return "".join(out)


def clean_pdb(input_pdb: Path, output_pdb: Path, *, timeout_sec: int = 120) -> Path:
    """Run pdb4amber then strip 5'-terminal phosphates. Return path to cleaned PDB."""
    p4a = shutil.which("pdb4amber")
    if p4a is None:
        raise Pdb4AmberNotFoundError(
            "pdb4amber not found on PATH. Activate the conda env that has AmberTools."
        )
    output_pdb = Path(output_pdb)
    output_pdb.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [p4a, "-i", str(input_pdb), "-o", str(output_pdb), "--reduce", "--no-conect"],
        capture_output=True, text=True, timeout=timeout_sec,
    )
    if result.returncode != 0 or not output_pdb.exists():
        raise Pdb4AmberFailedError(
            f"pdb4amber failed (rc={result.returncode}).\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    # Post-process: strip 5'-terminal phosphates that tleap cannot type-assign
    cleaned = _strip_5prime_phosphates(output_pdb.read_text())
    output_pdb.write_text(cleaned)

    return output_pdb
