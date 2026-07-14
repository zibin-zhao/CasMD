# Scientific background

## What an MD trajectory represents

Molecular dynamics integrates atomic motion under a molecular-mechanics force
field. A trajectory is a time-ordered simulation, not a collection of
independent experimental observations. Neighboring frames are autocorrelated.

This matters when comparing variants: thousands of frames from one trajectory
still represent one simulation run. Replicate-level inference requires multiple
independently initialized runs for every condition.

## StrandMD's validated protocol

| Component | Model |
|---|---|
| Protein | AMBER ff19SB |
| RNA | OL3 |
| DNA | parmbsc1 |
| Water | TIP3P |
| Box | Rectangular explicit solvent, 12 Å default padding |
| Temperature | 310.15 K default |
| Equilibration | 500 ps NVT + 500 ps NPT |
| Production | 500 ns default |
| Output interval | 100 ps default |

Only parameters carried into generated build or run files appear in the active
configuration UI. Alternative force fields are hidden until they have their own
end-to-end validation fixtures.

## Structure prediction is a starting point

AlphaFold Server, Boltz-2, and Protenix can propose complex structures.
Prediction confidence describes the prediction, not simulation convergence or
biochemical activity. Inspect chain assignment, missing atoms, termini, and
unsupported residues before trusting a build.

## Core analysis concepts

**RMSD** summarizes global structural displacement from a reference after
alignment. A plateau can support stability but does not prove equilibrium.

**RMSF** summarizes positional fluctuation by residue. Truncations or insertions
must be compared using residue identity or sequence alignment, not by blindly
truncating arrays to equal length.

**Radius of gyration (Rg)** summarizes compactness. Similar Rg values do not
guarantee that interfaces or local structure are preserved.

**Contacts and hydrogen bonds** describe geometric occupancy under explicit
cutoffs. Contact counts are not binding free energies and may depend strongly on
atom selections and system composition.

## Interpretation rules

- Discard the declared equilibration region before summary calculations.
- Compare physical time axes, not frame indices, when output frequencies differ.
- Treat two single trajectories as a descriptive comparison.
- Use independent replicate summaries for uncertainty and inferential tests.
- Use MD to prioritize wet-lab measurements, not replace them.

## Community tools

StrandMD orchestrates established tools rather than replacing them:

- AlphaFold Server, Boltz-2, and Protenix for structure prediction
- AmberTools and ParmEd for preparation and topology conversion
- GROMACS for simulation
- MDAnalysis for trajectory analysis
- Plotly and Streamlit for the interactive interface
