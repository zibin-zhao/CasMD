"""Format sequences for submission to the three online predictors.

This is the 'link out' half of the hybrid model: CasMD writes
submission-ready files and prints the server URLs; the user pastes
into the web UIs manually.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json


SERVER_URLS = {
    "boltz": "https://tamarind.bio/boltz-2",
    "protenix": "https://www.bioos.com/protenix",
    "af3": "https://alphafoldserver.com",
}


@dataclass(frozen=True)
class PrepResult:
    boltz_input: Path
    protenix_input: Path
    af3_input: Path


def prep_inputs(
    *,
    protein_fasta: str,
    rna_sequence: str | None,
    dna_sequence: str | None,
    target_complement: str | None,
    output_dir: Path,
    job_name: str,
) -> PrepResult:
    """Write three submission files (one per backend) ready to paste."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    protein_seq = _fasta_to_seq(protein_fasta)

    # ---- Boltz-2 input (YAML-like sequence block) ----
    boltz_lines = ["sequences:"]
    boltz_lines.append("  - protein:")
    boltz_lines.append("      id: A")
    boltz_lines.append(f"      sequence: {protein_seq}")
    chain_id = ord("B")
    if rna_sequence:
        boltz_lines.append("  - rna:")
        boltz_lines.append(f"      id: {chr(chain_id)}")
        boltz_lines.append(f"      sequence: {rna_sequence}")
        chain_id += 1
    if dna_sequence:
        boltz_lines.append("  - dna:")
        boltz_lines.append(f"      id: {chr(chain_id)}")
        boltz_lines.append(f"      sequence: {dna_sequence}")
        chain_id += 1
    if target_complement:
        boltz_lines.append("  - dna:")
        boltz_lines.append(f"      id: {chr(chain_id)}")
        boltz_lines.append(f"      sequence: {target_complement}")
    boltz_path = output_dir / "boltz_input.yaml"
    boltz_path.write_text("\n".join(boltz_lines) + "\n")

    # ---- Protenix input (JSON) — uses proteinChain/rnaSequence/dnaSequence keys ----
    protenix_seqs: list[dict] = [
        {"proteinChain": {"sequence": protein_seq, "count": 1}}
    ]
    if rna_sequence:
        protenix_seqs.append({"rnaSequence": {"sequence": rna_sequence, "count": 1}})
    if dna_sequence:
        protenix_seqs.append({"dnaSequence": {"sequence": dna_sequence, "count": 1}})
    if target_complement:
        protenix_seqs.append({"dnaSequence": {"sequence": target_complement, "count": 1}})
    protenix_input = [{"name": job_name, "covalent_bonds": [], "sequences": protenix_seqs}]
    protenix_path = output_dir / "protenix_input.json"
    protenix_path.write_text(json.dumps(protenix_input, indent=2))

    # ---- AF3 input (AlphaFold Server JSON schema — list wrapper + dialect/version) ----
    af3_seqs: list[dict] = [
        {"proteinChain": {"sequence": protein_seq, "count": 1, "useStructureTemplate": False}}
    ]
    if rna_sequence:
        af3_seqs.append({"rnaSequence": {"sequence": rna_sequence, "count": 1}})
    if dna_sequence:
        af3_seqs.append({"dnaSequence": {"sequence": dna_sequence, "count": 1}})
    if target_complement:
        af3_seqs.append({"dnaSequence": {"sequence": target_complement, "count": 1}})
    af3_input = [
        {
            "name": job_name,
            "modelSeeds": [],
            "sequences": af3_seqs,
            "dialect": "alphafoldserver",
            "version": 3,
        }
    ]
    af3_path = output_dir / "af3_input.json"
    af3_path.write_text(json.dumps(af3_input, indent=2))

    return PrepResult(
        boltz_input=boltz_path,
        protenix_input=protenix_path,
        af3_input=af3_path,
    )


def _fasta_to_seq(fasta: str) -> str:
    """Strip header lines from a FASTA, return concatenated sequence."""
    lines = [ln.strip() for ln in fasta.strip().splitlines()]
    return "".join(ln for ln in lines if not ln.startswith(">"))
