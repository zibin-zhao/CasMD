"""Parse + classify FASTA sequences for the Stage 1 sequence inputs."""
from __future__ import annotations


# Amino-acid letters that DON'T appear in standard nucleic-acid alphabets.
# Presence of any of these in a sequence ⇒ protein.
_PROTEIN_SPECIFIC = set("DEFHIKLMPQRSVWY")


def classify_sequence(seq: str) -> str | None:
    """Classify a sequence string as 'protein' / 'rna' / 'dna' / None.

    Heuristic:
    - Contains any protein-specific amino acid letter → protein
    - Contains U but not T → RNA
    - Contains T but not U → DNA
    - Only A/G/C (no T or U) → DNA (most common case)
    - Empty or unclassifiable → None
    """
    if not seq:
        return None
    chars = set(seq.upper()) - {"N", "X", "-", "*", " "}
    if not chars:
        return None
    if chars & _PROTEIN_SPECIFIC:
        return "protein"
    has_u = "U" in chars
    has_t = "T" in chars
    if has_u and not has_t:
        return "rna"
    if has_t and not has_u:
        return "dna"
    # Only A/G/C → ambiguous, default DNA
    if chars <= {"A", "G", "C"}:
        return "dna"
    return None


def parse_fasta(text: str) -> dict[str, list[str]]:
    """Parse FASTA text into {'protein': [...], 'rna': [...], 'dna': [...]}.

    Empty/missing categories are kept as empty lists for downstream stability.
    """
    sequences: list[tuple[str, str]] = []
    current_header: str | None = None
    current_seq: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            if current_header is not None:
                sequences.append((current_header, "".join(current_seq)))
            current_header = stripped[1:]
            current_seq = []
        else:
            current_seq.append(stripped.upper())
    if current_header is not None:
        sequences.append((current_header, "".join(current_seq)))

    out: dict[str, list[str]] = {"protein": [], "rna": [], "dna": []}
    for _header, seq in sequences:
        kind = classify_sequence(seq)
        if kind in out:
            out[kind].append(seq)
    return out


def fasta_to_form_fields(parsed: dict[str, list[str]]) -> dict[str, str]:
    """Convert parse_fasta output into the four Stage 1 form fields.

    Returns: {'protein_fasta': '...', 'rna_seq': '...', 'dna_seq': '...', 'target_seq': '...'}
    Values may be empty strings.
    """
    proteins = parsed.get("protein", [])
    rnas = parsed.get("rna", [])
    dnas = parsed.get("dna", [])
    return {
        # Wrap protein back into FASTA form so the text area shows it cleanly
        "protein_fasta": (">protein\n" + proteins[0]) if proteins else "",
        "rna_seq": rnas[0] if rnas else "",
        "dna_seq": dnas[0] if dnas else "",
        "target_seq": dnas[1] if len(dnas) >= 2 else "",
    }
