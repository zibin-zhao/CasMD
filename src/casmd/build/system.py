"""Top-level: PDB -> GROMACS-ready system."""
from __future__ import annotations
from dataclasses import dataclass, replace
from pathlib import Path

from casmd.build.chains import detect_chains
from casmd.build.tleap_recipe import generate_tleap_input, BuildConfig
from casmd.build.tleap_runner import run_tleap
from casmd.build.gromacs_convert import amber_to_gromacs
from casmd.build.pdb_prep import clean_pdb
from casmd.build.ions import ion_counts_for_salt
from casmd.build.water_count import count_waters


def _resolve_salt_counts(config: BuildConfig, n_water: int) -> BuildConfig:
    """Return a copy of config with ion_extra_cation/anion filled in from
    salt_molarity + the measured water count."""
    counts = ion_counts_for_salt(
        cation=config.ion_cation, anion=config.ion_anion,
        molarity=config.salt_molarity, n_water=n_water,
    )
    return replace(config,
                   ion_extra_cation=counts.extra_cation,
                   ion_extra_anion=counts.extra_anion)


@dataclass(frozen=True)
class SystemBundle:
    """Paths to every file produced by `build_system`."""
    top: Path
    gro: Path
    solvated_pdb: Path
    prmtop: Path
    inpcrd: Path
    tleap_recipe: Path
    cleaned_pdb: Path


def build_system(
    pdb_path: Path,
    output_dir: Path,
    config: BuildConfig,
    *,
    prefix: str = "system",
) -> SystemBundle:
    """PDB → pdb4amber → tleap → AMBER → GROMACS. Returns paths to all outputs."""
    pdb_path = Path(pdb_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_pdb = clean_pdb(pdb_path, output_dir / f"{prefix}_cleaned.pdb")
    chains = detect_chains(cleaned_pdb)

    if config.salt_molarity > 0:
        # Pass A: solvate + neutralize only, to count waters.
        neutral_cfg = replace(config, salt_molarity=0.0,
                              ion_extra_cation=0, ion_extra_anion=0)
        recipe_a = generate_tleap_input(
            str(cleaned_pdb.resolve()), f"{prefix}_neutral", chains, neutral_cfg,
        )
        run_tleap(recipe_a, output_dir, output_prefix=f"{prefix}_neutral")
        n_water = count_waters(output_dir / f"{prefix}_neutral_solvated.pdb")
        config = _resolve_salt_counts(config, n_water)

    # Final pass (or the only pass when molarity == 0).
    recipe = generate_tleap_input(str(cleaned_pdb.resolve()), prefix, chains, config)
    prmtop, inpcrd = run_tleap(recipe, output_dir, output_prefix=prefix)
    top, gro = amber_to_gromacs(prmtop, inpcrd, output_dir, prefix=prefix)

    return SystemBundle(
        top=top,
        gro=gro,
        solvated_pdb=output_dir / f"{prefix}_solvated.pdb",
        prmtop=prmtop,
        inpcrd=inpcrd,
        tleap_recipe=output_dir / f"{prefix}.in",
        cleaned_pdb=cleaned_pdb,
    )
