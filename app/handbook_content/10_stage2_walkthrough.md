# Stage 2 walkthrough — Results & Visualization

After your HPC simulation finishes and you've run the included `analyze.py`
script on the trajectory, return to CasMD with the analysis output.

## Upload

Upload the analysis output zip (containing `results.json`, `rmsd.dat`,
`rmsf.dat`, `rg.dat`, and `figures/`). CasMD auto-detects each file.

## What you'll see

- **Prediction confidence cards** — iPTM / pTM / pLDDT from your Stage 1
  selection.
- **Trajectory KPI cards** — frames, equilibration discard, mean RMSD,
  mean RMSF, mean Rg.
- **Interactive Plotly charts** — RMSD over time, RMSF per residue, Rg over
  time. Hover, zoom, pan.
- **Report generation** — Generate DOCX or PPTX with one click.

## Reading the numbers

- **RMSD (root mean square deviation)** — how much the protein has moved from
  the starting structure. Lower = more stable. > 5 Å suggests significant
  conformational change.
- **RMSF (root mean square fluctuation)** — per-residue flexibility. High
  RMSF = flexible loops; low RMSF = rigid core.
- **Rg (radius of gyration)** — how compact the protein is. A sudden Rg jump
  suggests unfolding.
