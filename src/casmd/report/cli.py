"""`casmd-report` CLI: generate DOCX + PPTX from analyze.py outputs."""
from __future__ import annotations
import argparse
from pathlib import Path

from casmd.report.data import ReportData, PredictionSummary, load_analysis_json
from casmd.report.docx_writer import generate_docx
from casmd.report.pptx_writer import generate_pptx


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="casmd-report",
        description="Generate DOCX + PPTX report from analyze.py outputs.",
    )
    p.add_argument("results_json", type=Path, help="Path to results.json from analyze.py")
    p.add_argument("--figures-dir", type=Path, required=True,
                   help="Directory containing rmsd.png / rmsf.png / rg.png")
    p.add_argument("--name", default="casmd_run", help="Job name to display")
    p.add_argument("--production-ns", type=float, default=100.0,
                   help="Production length in ns (for the header)")
    p.add_argument("--interpretation",
                   default="Equilibrated protein metrics summarized below.",
                   help="One-paragraph interpretation")
    # Optional prediction metadata
    p.add_argument("--pred-backend", help="Prediction backend label (e.g. 'protenix')")
    p.add_argument("--pred-model", type=int, default=0)
    p.add_argument("--pred-iptm", type=float)
    p.add_argument("--pred-ptm", type=float)
    p.add_argument("--pred-plddt", type=float)
    # Outputs
    p.add_argument("--docx", type=Path, help="Output DOCX path (omit to skip)")
    p.add_argument("--pptx", type=Path, help="Output PPTX path (omit to skip)")
    args = p.parse_args(argv)

    if args.docx is None and args.pptx is None:
        print("Nothing to do — pass --docx and/or --pptx.")
        return 2

    analysis = load_analysis_json(args.results_json)
    prediction = None
    if args.pred_backend:
        prediction = PredictionSummary(
            backend=args.pred_backend,
            model_id=args.pred_model,
            iptm=args.pred_iptm,
            ptm=args.pred_ptm,
            plddt_mean=args.pred_plddt,
        )

    figures: dict[str, Path] = {}
    for key in ("rmsd", "rmsf", "rg"):
        fig = args.figures_dir / f"{key}.png"
        if fig.exists():
            figures[key] = fig

    data = ReportData(
        job_name=args.name,
        production_ns=args.production_ns,
        prediction=prediction,
        analysis=analysis,
        figures=figures,
        interpretation=args.interpretation,
    )

    if args.docx is not None:
        generate_docx(data, args.docx)
        print(f"DOCX: {args.docx}")
    if args.pptx is not None:
        generate_pptx(data, args.pptx)
        print(f"PPTX: {args.pptx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
