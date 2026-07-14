"""Sequence-aware residue alignment between two trajectories."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ResidueAlignment:
    """Pairwise alignment between system A and system B chains.

    a_to_b maps A's 1-based residue index to B's (or None if gap).
    b_to_a is the reverse.
    aligned_segments lists (a_start, a_end, b_start, b_end) for each
    contiguous matching block (1-based, inclusive).
    """
    identity_pct: float
    a_to_b: dict[int, int | None]
    b_to_a: dict[int, int | None]
    aligned_segments: list[tuple[int, int, int, int]]


try:
    from Bio import pairwise2
    from Bio.Align import substitution_matrices
    _BLOSUM62 = substitution_matrices.load("BLOSUM62")
except ImportError as e:
    raise ImportError(
        "casmd.report.align requires biopython. Install with "
        "`pip install biopython`."
    ) from e


# Standard pairwise gap penalties used by most protein aligners.
_GAP_OPEN = -10.0
_GAP_EXTEND = -0.5


def sequence_align(seq_a: str, seq_b: str) -> ResidueAlignment:
    """Pairwise global alignment of two protein sequences via BLOSUM62.

    Returns a ResidueAlignment with:
    - identity_pct: fraction of aligned positions that match exactly
      (gaps don't count as matches)
    - a_to_b, b_to_a: residue-index maps (1-based)
    - aligned_segments: contiguous matching blocks
    """
    alignments = pairwise2.align.globalds(
        seq_a, seq_b, _BLOSUM62, _GAP_OPEN, _GAP_EXTEND, one_alignment_only=True
    )
    if not alignments:
        # Pathological: alignment failed entirely
        return ResidueAlignment(
            identity_pct=0.0, a_to_b={}, b_to_a={}, aligned_segments=[]
        )

    aln = alignments[0]
    aligned_a = aln.seqA
    aligned_b = aln.seqB

    a_to_b: dict[int, int | None] = {}
    b_to_a: dict[int, int | None] = {}
    matches = 0
    aligned_positions = 0

    a_idx = 0   # 1-based position in seq_a, advanced when not '-'
    b_idx = 0

    segments: list[tuple[int, int, int, int]] = []
    seg_start_a: int | None = None
    seg_start_b: int | None = None
    seg_last_a: int | None = None
    seg_last_b: int | None = None

    for ca, cb in zip(aligned_a, aligned_b):
        if ca != "-":
            a_idx += 1
        if cb != "-":
            b_idx += 1

        if ca != "-" and cb != "-":
            a_to_b[a_idx] = b_idx
            b_to_a[b_idx] = a_idx
            aligned_positions += 1
            if ca == cb:
                matches += 1
            # Track segment
            if seg_start_a is None:
                seg_start_a, seg_start_b = a_idx, b_idx
            seg_last_a, seg_last_b = a_idx, b_idx
        else:
            if ca != "-":
                a_to_b[a_idx] = None
            if cb != "-":
                b_to_a[b_idx] = None
            # Close the current segment if any
            if seg_start_a is not None:
                segments.append((seg_start_a, seg_last_a, seg_start_b, seg_last_b))
                seg_start_a = seg_start_b = seg_last_a = seg_last_b = None

    if seg_start_a is not None:
        segments.append((seg_start_a, seg_last_a, seg_start_b, seg_last_b))

    identity_pct = matches / aligned_positions if aligned_positions > 0 else 0.0

    return ResidueAlignment(
        identity_pct=identity_pct,
        a_to_b=a_to_b,
        b_to_a=b_to_a,
        aligned_segments=segments,
    )
