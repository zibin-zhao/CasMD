"""Rank and select prediction models across one or more bundles."""
from __future__ import annotations
from typing import Sequence

from casmd.predict.model import PredictionBundle, PredictionModel


def rank(bundles: Sequence[PredictionBundle], by: str = "iptm") -> list[PredictionModel]:
    """Return all models with non-None `by` score, sorted descending by it."""
    pool: list[PredictionModel] = []
    for b in bundles:
        pool.extend(b.models)
    pool = [m for m in pool if getattr(m, by) is not None]
    pool.sort(key=lambda m: getattr(m, by), reverse=True)
    return pool


def select_best(bundles: Sequence[PredictionBundle], by: str = "iptm") -> PredictionModel:
    """Return the single highest-scoring model across all bundles."""
    ranked = rank(bundles, by=by)
    if not ranked:
        raise ValueError(f"no models with a non-None {by!r} score")
    return ranked[0]
