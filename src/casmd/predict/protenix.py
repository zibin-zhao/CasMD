"""Parse Protenix downloaded prediction bundles.

Layout (per fixture):
    <bundle_dir>/
    ├── inputs.json
    └── protenix_prediction_<hash>/
        └── seed_<N>/
            └── predictions/
                ├── protenix_prediction_<hash>_sample_N.cif
                └── protenix_prediction_<hash>_summary_confidence_sample_N.json
"""
from __future__ import annotations
import json
import re
from pathlib import Path

from casmd.predict.model import PredictionBundle, PredictionModel
from casmd.predict.cif_utils import cif_to_pdb


_SEED_RE = re.compile(r"seed_(\d+)$")
_SAMPLE_RE = re.compile(r"_sample_(\d+)$")


def parse_protenix(bundle_dir: Path) -> PredictionBundle:
    bundle_dir = Path(bundle_dir)
    seed_dirs = [p for p in bundle_dir.rglob("seed_*") if p.is_dir()]
    if not seed_dirs:
        raise FileNotFoundError(f"no seed_<N> dir under {bundle_dir}")

    models: list[PredictionModel] = []
    for seed_dir in sorted(seed_dirs):
        m = _SEED_RE.search(seed_dir.name)
        seed = int(m.group(1)) if m else None
        preds_dir = seed_dir / "predictions"
        if not preds_dir.is_dir():
            continue

        # Collect CIF files (convert to PDB as needed)
        cif_files = sorted(preds_dir.glob("*.cif"))
        pdb_files_existing = sorted(preds_dir.glob("*.pdb"))

        struct_files: list[Path] = []
        if pdb_files_existing:
            struct_files = pdb_files_existing
        else:
            for cif in cif_files:
                pdb = cif.with_suffix(".pdb")
                if not pdb.exists():
                    cif_to_pdb(cif, pdb)
                struct_files.append(pdb)

        # Build a map: sample_index -> json path
        sample_json: dict[int, Path] = {}
        for jf in preds_dir.glob("*.json"):
            sm = _SAMPLE_RE.search(jf.stem)
            if sm:
                sample_json[int(sm.group(1))] = jf

        for struct in struct_files:
            sm = _SAMPLE_RE.search(struct.stem)
            sample_idx = int(sm.group(1)) if sm else None
            # Infer model_id from sample index (or fallback to position)
            model_id = sample_idx if sample_idx is not None else struct_files.index(struct)

            iptm = ptm = plddt = None
            json_path = sample_json.get(sample_idx) if sample_idx is not None else None
            if json_path is not None:
                try:
                    with json_path.open() as f:
                        d = json.load(f)
                    iptm = _get_metric(d, ("iptm",))
                    ptm = _get_metric(d, ("ptm",))
                    plddt = _get_metric(d, ("plddt",))
                except Exception:
                    pass

            models.append(PredictionModel(
                pdb_path=struct.resolve(),
                backend="protenix",
                model_id=model_id,
                seed=seed,
                iptm=iptm,
                ptm=ptm,
                plddt_mean=plddt,
            ))

    if not models:
        raise ValueError(f"no models found under {bundle_dir}")
    return PredictionBundle(backend="protenix", raw_dir=bundle_dir.resolve(), models=tuple(models))


def _get_metric(d: dict, keys: tuple[str, ...]) -> float | None:
    for k in keys:
        if k in d:
            v = d[k]
            if isinstance(v, (int, float)):
                return float(v)
    return None
