"""Parse AlphaFold Server (AF3) downloaded bundles.

Layout:
    <bundle_dir>/
    ├── fold_<name>_model_<i>.cif
    ├── fold_<name>_summary_confidences_<i>.json
    ├── fold_<name>_full_data_<i>.json  (optional)
    └── fold_<name>_job_request.json
"""
from __future__ import annotations
import json
import re
from pathlib import Path

from casmd.predict.model import PredictionBundle, PredictionModel
from casmd.predict.cif_utils import cif_to_pdb


_MODEL_RE = re.compile(r"_model_(\d+)\.cif$")
_CONF_RE = re.compile(r"_summary_confidences_(\d+)\.json$")


def parse_af3(bundle_dir: Path) -> PredictionBundle:
    bundle_dir = Path(bundle_dir)
    if not bundle_dir.is_dir():
        raise FileNotFoundError(bundle_dir)

    # Group cif + confidence files by model index
    cif_by_idx: dict[int, Path] = {}
    conf_by_idx: dict[int, Path] = {}
    for p in bundle_dir.iterdir():
        m1 = _MODEL_RE.search(p.name)
        if m1:
            cif_by_idx[int(m1.group(1))] = p
            continue
        m2 = _CONF_RE.search(p.name)
        if m2:
            conf_by_idx[int(m2.group(1))] = p

    if not cif_by_idx:
        raise ValueError(f"no AF3 model CIFs under {bundle_dir}")

    models: list[PredictionModel] = []
    for idx in sorted(cif_by_idx):
        cif = cif_by_idx[idx]
        pdb = cif.with_suffix(".pdb")
        if not pdb.exists():
            cif_to_pdb(cif, pdb)

        iptm = ptm = plddt = None
        if idx in conf_by_idx:
            with conf_by_idx[idx].open() as f:
                d = json.load(f)
            iptm = _get(d, ("iptm",))
            ptm = _get(d, ("ptm",))
            plddt = _get(d, ("plddt", "mean_plddt"))
        models.append(PredictionModel(
            pdb_path=pdb.resolve(),
            backend="af3",
            model_id=idx,
            seed=None,
            iptm=iptm,
            ptm=ptm,
            plddt_mean=plddt,
        ))
    return PredictionBundle(backend="af3", raw_dir=bundle_dir.resolve(), models=tuple(models))


def _get(d: dict, keys: tuple[str, ...]) -> float | None:
    for k in keys:
        if k in d and isinstance(d[k], (int, float)):
            return float(d[k])
    return None
