"""`casmd-predict` CLI: prep / ingest / select."""
from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path

from casmd.predict.prep import prep_inputs, SERVER_URLS
from casmd.predict.boltz2 import parse_boltz2
from casmd.predict.protenix import parse_protenix
from casmd.predict.af3 import parse_af3
from casmd.predict.selector import select_best, rank


_PARSERS = {
    "boltz": parse_boltz2,
    "boltz-2": parse_boltz2,
    "protenix": parse_protenix,
    "af3": parse_af3,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="casmd-predict")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prep = sub.add_parser("prep", help="Write submission-ready inputs for all 3 servers.")
    p_prep.add_argument("name", help="Job name (used as filename / title)")
    p_prep.add_argument("--protein", type=Path, required=True, help="Protein FASTA file")
    p_prep.add_argument("--rna", help="RNA sequence (single line)")
    p_prep.add_argument("--dna", help="DNA sequence (single line)")
    p_prep.add_argument("--target", help="DNA target-complement sequence")
    p_prep.add_argument("-o", "--output", type=Path, required=True, help="Output directory")

    p_ing = sub.add_parser("ingest", help="Parse a downloaded prediction bundle.")
    p_ing.add_argument("bundle_dir", type=Path)
    p_ing.add_argument("--backend", required=True, choices=list(_PARSERS.keys()))

    p_sel = sub.add_parser("select", help="Pick best model across one or more bundles.")
    p_sel.add_argument("bundles", type=str, nargs="+",
                       help="Paths in the form '<backend>:<dir>', e.g. 'af3:./af3_run/'")
    p_sel.add_argument("-o", "--output", type=Path, required=True, help="Where to copy the best PDB")
    p_sel.add_argument("--by", default="iptm", choices=["iptm", "ptm", "plddt_mean"])

    args = parser.parse_args(argv)

    if args.cmd == "prep":
        result = prep_inputs(
            protein_fasta=args.protein.read_text(),
            rna_sequence=args.rna,
            dna_sequence=args.dna,
            target_complement=args.target,
            output_dir=args.output,
            job_name=args.name,
        )
        print(f"Wrote:\n  {result.boltz_input}\n  {result.protenix_input}\n  {result.af3_input}")
        print("\nSubmit at:")
        for k, url in SERVER_URLS.items():
            print(f"  {k:9s} -> {url}")
        return 0

    if args.cmd == "ingest":
        bundle = _PARSERS[args.backend](args.bundle_dir)
        print(f"Parsed {len(bundle.models)} models from {bundle.backend}")
        for m in bundle.models:
            iptm = f"{m.iptm:.3f}" if m.iptm is not None else " -- "
            ptm = f"{m.ptm:.3f}" if m.ptm is not None else " -- "
            print(f"  model {m.model_id}  iPTM={iptm}  pTM={ptm}  -> {m.pdb_path}")
        return 0

    if args.cmd == "select":
        bundles = []
        for spec in args.bundles:
            parts = spec.split(":", 1)
            if len(parts) != 2:
                print(f"error: bundle spec must be '<backend>:<dir>', got {spec!r}", file=sys.stderr)
                return 2
            backend, dirpath = parts
            if backend not in _PARSERS:
                print(f"error: unknown backend {backend!r}", file=sys.stderr)
                return 2
            bundles.append(_PARSERS[backend](Path(dirpath)))
        best = select_best(bundles, by=args.by)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(best.pdb_path, args.output)
        score = getattr(best, args.by)
        print(f"Best: {best.backend} model {best.model_id}  {args.by}={score:.3f}")
        print(f"Copied to: {args.output}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
