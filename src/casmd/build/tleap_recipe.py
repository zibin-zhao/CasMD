"""Generate tleap input files matching CHARMM-GUI Solution Builder defaults."""
from __future__ import annotations
from dataclasses import dataclass

from casmd.build.chains import ChainKind


@dataclass(frozen=True)
class BuildConfig:
    """Validated defaults for protein–nucleic-acid systems."""
    protein_ff: str = "ff19SB"
    rna_ff: str = "OL3"
    dna_ff: str = "bsc1"
    water_ff: str = "tip3p"
    box_padding_A: float = 12.0
    box_shape: str = "rectangular"  # tleap: solvateBox = rect, solvateOct = octahedral
    ion_cation: str = "Na+"
    ion_anion: str = "Cl-"
    salt_molarity: float = 0.0       # 0 = neutralize only; >0 -> compute counts at build time
    ion_extra_cation: int = 0        # explicit extra cations (set by the two-pass orchestrator)
    ion_extra_anion: int = 0         # explicit extra anions


_LEAPRC = {
    "ff19SB": "leaprc.protein.ff19SB",
    "ff14SB": "leaprc.protein.ff14SB",
    "OL3": "leaprc.RNA.OL3",
    "DESRES-RNA": "leaprc.RNA.shaw",  # placeholder; verify in tleap
    "bsc1": "leaprc.DNA.bsc1",
    "OL15": "leaprc.DNA.OL15",
    "parmbsc0": "leaprc.DNA.bsc0",
    "tip3p": "leaprc.water.tip3p",
    "TIP4P-EW": "leaprc.water.tip4pew",
    "OPC": "leaprc.water.opc",
}


def generate_tleap_input(
    pdb_path: str,
    output_prefix: str,
    chains: dict[str, ChainKind],
    config: BuildConfig,
) -> str:
    """Build the tleap input script as a string.

    Args:
        pdb_path: path to the input PDB (e.g. AF3/Boltz-2 output).
        output_prefix: written as `<prefix>.prmtop` and `<prefix>.inpcrd`.
        chains: chain-type map from `detect_chains`.
        config: force-field + solvation settings.
    """
    kinds = set(chains.values())
    lines: list[str] = []

    # Force fields — only load what's needed
    if ChainKind.PROTEIN in kinds:
        lines.append(f"source {_LEAPRC[config.protein_ff]}")
    if ChainKind.RNA in kinds:
        lines.append(f"source {_LEAPRC[config.rna_ff]}")
    if ChainKind.DNA in kinds:
        lines.append(f"source {_LEAPRC[config.dna_ff]}")
    lines.append(f"source {_LEAPRC[config.water_ff]}")
    lines.append("")

    # Load structure
    lines.append(f"sys = loadpdb {pdb_path}")
    lines.append("")

    # Solvate
    solvate_cmd = "solvateBox" if config.box_shape == "rectangular" else "solvateOct"
    water_box = "TIP3PBOX" if config.water_ff == "tip3p" else "OPCBOX"
    lines.append(f"{solvate_cmd} sys {water_box} {config.box_padding_A}")
    lines.append("")

    # Neutralize, then add any explicit salt ions.
    lines.append(f"addIonsRand sys {config.ion_cation} 0")
    lines.append(f"addIonsRand sys {config.ion_anion} 0")
    if config.ion_extra_cation > 0:
        lines.append(f"addIonsRand sys {config.ion_cation} {config.ion_extra_cation}")
    if config.ion_extra_anion > 0:
        lines.append(f"addIonsRand sys {config.ion_anion} {config.ion_extra_anion}")
    lines.append("")

    # Save AMBER topology + coords
    lines.append(f"saveAmberParm sys {output_prefix}.prmtop {output_prefix}.inpcrd")
    lines.append(f"savePdb sys {output_prefix}_solvated.pdb")
    lines.append("quit")
    lines.append("")

    return "\n".join(lines)
