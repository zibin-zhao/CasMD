# Running analyze.py after MD

The `analyze.py` script bundled with every CasMD job computes three core
metrics: **RMSD, RMSF, Rg**.

## Usage

```bash
python analyze.py --tpr md.tpr --xtc md.xtc -o analysis/
```

## What it does

1. Loads the trajectory with MDAnalysis.
2. Discards the first 20% of frames as equilibration.
3. Computes:
   - **Protein Cα RMSD** vs the first frame — saved to `rmsd.dat` + plotted.
   - **Per-residue RMSF** for the equilibrated portion — saved to `rmsf.dat`.
   - **Protein radius of gyration** over time — saved to `rg.dat`.
4. Writes a summary `results.json` with mean values + frame counts.
5. Writes three PNG figures in `figures/`.

## Output structure

```
analysis/
├── results.json
├── rmsd.dat, rmsf.dat, rg.dat
└── figures/
    ├── rmsd.png
    ├── rmsf.png
    └── rg.png
```

Zip the `analysis/` directory and upload to Stage 2 of the CasMD UI.
