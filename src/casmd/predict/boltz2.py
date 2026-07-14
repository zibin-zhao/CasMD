"""Parse Boltz-2 downloaded result bundles."""
from __future__ import annotations
import json
import re
from pathlib import Path

import numpy as np

from casmd.predict.model import PredictionBundle, PredictionModel


_MODEL_RE = re.compile(r"result_model_(\d+)\.pdb$")
_CONF_RE = re.compile(r"confidence_result_model_(\d+)\.json$")


def parse_boltz2(bundle_dir: Path) -> PredictionBundle:
    """Parse a Boltz-2 download bundle.

    Expects layout:
        <bundle_dir>/predictions/result/result_model_<i>.pdb
        <bundle_dir>/predictions/result/confidence_result_model_<i>.json
        <bundle_dir>/predictions/result/plddt_result_model_<i>.npz   (optional)
    """
    bundle_dir = Path(bundle_dir)
    results_dir = bundle_dir / "predictions" / "result"
    if not results_dir.is_dir():
        raise FileNotFoundError(f"missing {results_dir}")

    models: list[PredictionModel] = []
    for pdb in sorted(results_dir.glob("result_model_*.pdb")):
        m = _MODEL_RE.search(pdb.name)
        if not m:
            continue
        model_id = int(m.group(1))
        conf_path = results_dir / f"confidence_result_model_{model_id}.json"
        iptm = ptm = None
        if conf_path.exists():
            with conf_path.open() as f:
                conf = json.load(f)
            iptm = _extract_first_match(conf, ("iptm", "confidence_iptm", "complex_iptm"))
            ptm = _extract_first_match(conf, ("ptm", "confidence_ptm", "complex_ptm"))
        plddt_path = results_dir / f"plddt_result_model_{model_id}.npz"
        plddt_mean = None
        if plddt_path.exists():
            data = np.load(plddt_path)
            arr = data[data.files[0]] if data.files else None
            if arr is not None and arr.size:
                plddt_mean = float(arr.mean())
        models.append(PredictionModel(
            pdb_path=pdb.resolve(),
            backend="boltz-2",
            model_id=model_id,
            seed=None,
            iptm=iptm,
            ptm=ptm,
            plddt_mean=plddt_mean,
        ))
    if not models:
        raise ValueError(f"no models found under {results_dir}")
    models.sort(key=lambda m: m.model_id)
    return PredictionBundle(backend="boltz-2", raw_dir=bundle_dir.resolve(), models=tuple(models))


def _extract_first_match(d: dict, keys: tuple[str, ...]) -> float | None:
    for k in keys:
        if k in d:
            return float(d[k])
    return None
