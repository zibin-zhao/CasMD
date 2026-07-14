"""CIF -> PDB conversion (shared between Protenix and AF3 parsers)."""
from __future__ import annotations
from pathlib import Path


def cif_to_pdb(cif: Path, pdb_out: Path) -> Path:
    """Convert a mmCIF file to PDB. Returns the output path.

    Prefers gemmi (fast, no warnings); falls back to biopython.
    """
    cif = Path(cif)
    pdb_out = Path(pdb_out)
    pdb_out.parent.mkdir(parents=True, exist_ok=True)

    try:
        import gemmi
        st = gemmi.read_structure(str(cif))
        st.write_pdb(str(pdb_out))
        return pdb_out
    except ImportError:
        pass

    from Bio.PDB.MMCIFParser import MMCIFParser
    from Bio.PDB.PDBIO import PDBIO
    parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure(cif.stem, str(cif))
    io = PDBIO()
    io.set_structure(structure)
    io.save(str(pdb_out))
    return pdb_out
