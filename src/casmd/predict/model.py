"""Unified data model for prediction outputs across backends."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PredictionModel:
    """One predicted structure with its confidence metrics.

    iptm, ptm, plddt_mean are `None` when the backend does not report them.
    """
    pdb_path: Path
    backend: str          # 'boltz-2' | 'protenix' | 'af3'
    model_id: int
    seed: int | None
    iptm: float | None
    ptm: float | None
    plddt_mean: float | None


@dataclass(frozen=True)
class PredictionBundle:
    """All models from one prediction submission."""
    backend: str
    raw_dir: Path
    models: tuple[PredictionModel, ...]
