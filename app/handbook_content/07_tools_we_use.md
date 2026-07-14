# The tools we use

CasMD glues together several well-tested community tools. Each one is best-in-class
for its role.

## Structure prediction

- **AlphaFold 3 (AF3)** — Google DeepMind's structure predictor. Best-in-class
  accuracy on protein-nucleic acid complexes. Used via the AlphaFold Server.
- **Boltz-2** — Open-weight predictor from MIT/Genesis Therapeutics. Free to
  use and runs in ~10 minutes per prediction. Integrated via the Boltz
  Discovery web service.
- **Protenix** — ByteDance's open-weight predictor. Strong on multi-chain
  complexes. Integrated via bioos.com.

## System building

- **AmberTools** — `pdb4amber` cleans PDBs; `tleap` builds topologies; `parmed`
  converts between AMBER and GROMACS formats. CasMD uses all three.
- **pdb4amber** — Strips problematic atoms (e.g. 5'-terminal phosphates) so
  tleap can parameterize the structure.

## Simulation

- **GROMACS** — Fast, GPU-accelerated MD engine. CasMD generates GROMACS-format
  topologies and `.mdp` configuration files; you run the actual simulation
  on your HPC.

## Analysis

- **MDAnalysis** — Python library that reads GROMACS trajectories and computes
  metrics (RMSD, RMSF, Rg).
- **NumPy / matplotlib** — Underpin the analysis and figure generation.

## UI & reports

- **Streamlit** — The web framework powering the CasMD app.
- **Plotly** — Interactive plots in the dashboard.
- **python-docx, python-pptx** — Generate downloadable Word and PowerPoint reports.
- **Jinja2** — Templates the `.mdp` and SLURM files in each bundle.
