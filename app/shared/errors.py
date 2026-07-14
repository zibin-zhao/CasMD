"""Translate raw exceptions into plain-English user-facing messages."""
from __future__ import annotations


def friendly_error(exc: BaseException, *, context: str = "operation") -> str:
    """Map a known exception pattern to a one-sentence user-readable message.

    Falls back to ``str(exc)`` when nothing matches.
    """
    msg = str(exc).lower()

    # MDAnalysis: trajectory was water-stripped, topology kept water
    if "number of atoms" in msg and "same" in msg:
        return (
            "Your topology and trajectory have different atom counts. This "
            "usually means the trajectory was stripped of water but the "
            "topology kept it. Use `system.gro` or `md_solute.gro` (the "
            "matching solute-only topology) instead of `md.gro`."
        )

    # MDAnalysis: TPR format newer than installed parser
    if "tpx version" in msg and "not support" in msg:
        return (
            "Your GROMACS version produced a .tpr in a newer format than "
            "MDAnalysis can read. Pass the trajectory's matching .gro file "
            "instead — same data, no version lock."
        )

    # py7zr / extract dirs
    if isinstance(exc, (FileExistsError, NotADirectoryError)):
        return (
            "The archive couldn't be extracted cleanly (a path inside it is "
            "ambiguous between file and directory). Try re-packing as .zip "
            "or .tar.gz."
        )

    # tleap missing
    if "pdb4amber" in msg or "tleap" in msg or "not found on path" in msg:
        return (
            "The AmberTools binaries weren't on PATH for the build step. "
            "If running locally, activate the conda env that has AmberTools "
            "before launching casmd-ui."
        )

    # Fall back: just show the raw message
    return f"{context.capitalize()} failed: {exc}"
