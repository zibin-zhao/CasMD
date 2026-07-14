"""Convert a target salt molarity into AMBER ion counts.

The number of ion pairs at concentration C is computed from the number of
explicit water molecules using the molarity of pure water (55.5 mol/L):

    n_pairs = round(C * n_water / 55.5)

For a divalent cation (e.g. Mg2+ as MgCl2), the salt formula adds two anions
per cation, so n_anion = 2 * n_cation.
"""
from __future__ import annotations
from dataclasses import dataclass


# Molarity of pure water: 1000 g/L / 18.015 g/mol.
_WATER_MOLARITY = 55.5

# Cations that carry a +2 charge (relevant for MgCl2 / CaCl2 salts).
_DIVALENT_CATIONS = {"Mg2+", "MG2+", "Ca2+", "CA2+", "Zn2+", "ZN2+"}


@dataclass(frozen=True)
class IonCounts:
    """Extra ions to add on top of neutralization."""
    extra_cation: int
    extra_anion: int


def is_divalent(cation: str) -> bool:
    """True if the cation carries a +2 charge."""
    return cation in _DIVALENT_CATIONS


def ion_counts_for_salt(*, cation: str, anion: str,
                        molarity: float, n_water: int) -> IonCounts:
    """Return the extra ion pairs to add for the requested salt concentration.

    Args:
        cation: AMBER cation name (e.g. "Na+", "K+", "Mg2+").
        anion: AMBER anion name (e.g. "Cl-").
        molarity: target salt concentration in mol/L. 0 -> neutralize only.
        n_water: number of explicit water molecules in the solvated box.

    For a monovalent cation, returns equal cation/anion counts.
    For a divalent cation (MgCl2), returns n_anion = 2 * n_cation.
    """
    if molarity <= 0 or n_water <= 0:
        return IonCounts(extra_cation=0, extra_anion=0)

    n_formula = round(molarity * n_water / _WATER_MOLARITY)
    if is_divalent(cation):
        return IonCounts(extra_cation=n_formula, extra_anion=2 * n_formula)
    return IonCounts(extra_cation=n_formula, extra_anion=n_formula)
