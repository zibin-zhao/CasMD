# Glossary

**AlphaFold 3 (AF3)** — Google DeepMind's deep-learning structure predictor.

**AmberTools** — Suite of programs (`tleap`, `pdb4amber`, `parmed`, etc.) for
building MD systems with AMBER force fields.

**Atomistic** — Simulation where every atom is represented explicitly (as
opposed to coarse-grained, where groups of atoms are lumped together).

**BibTeX** — Bibliography format for LaTeX. CasMD shows BibTeX entries on
the Acknowledgements page for easy citation.

**Boltz-2** — Open-weight protein-structure prediction model.

**CHARMM-GUI** — Web service for building MD systems. CasMD replaces it
for protein-nucleic acid pipelines.

**CIF** — Crystallographic Information File format. Modern alternative
to PDB for structure data.

**Conformation** — A specific 3D arrangement of a molecule's atoms.

**crRNA** — CRISPR RNA. The guide RNA that pairs with the target.

**Equilibration** — The early phase of an MD simulation where the system
relaxes toward thermal equilibrium. Typically the first 20% is discarded.

**ff19SB** — AMBER's 2019 protein force field.

**Force field** — Mathematical model of inter-atomic forces.

**GROMACS** — Open-source MD engine, GPU-accelerated.

**Guide RNA** — RNA that directs a Cas protein to its target nucleic acid.

**Handle (crRNA)** — The 5' end of a crRNA that binds the Cas protein.

**iPTM** — Interface Predicted Template Modeling score. Confidence in the
predicted interface between two chains. 0–1, higher = better.

**Ions (neutralizing)** — Na⁺ or Cl⁻ added to balance the net charge of the
solvated system.

**LINCS** — Linear constraint solver. Used by GROMACS to constrain bond lengths
during MD.

**MDAnalysis** — Python library for reading and analyzing MD trajectories.

**NPT** — Constant Number, Pressure, Temperature ensemble.

**NVT** — Constant Number, Volume, Temperature ensemble.

**OL3** — RNA force field, paired with ff19SB for protein-RNA simulation.

**parmed** — Converts AMBER topologies to GROMACS format.

**pdb4amber** — Cleans PDB files for AMBER's tleap.

**Periodic boundary condition (PBC)** — Treats the simulation box as
repeating in all directions, avoiding edge effects.

**pLDDT** — predicted Local Distance Difference Test. Per-residue confidence
metric from structure predictors. 0–100, higher = better.

**pTM** — Predicted Template Modeling score. Overall structure confidence.
0–1, higher = better.

**Protenix** — ByteDance's open-weight structure predictor.

**RMSD** — Root Mean Square Deviation. How much a structure has moved
from a reference. Units: ångströms.

**RMSF** — Root Mean Square Fluctuation. Per-residue flexibility.

**Rg** — Radius of gyration. How compact / extended a molecule is.

**SLURM** — Job scheduler used on most HPC clusters.

**Solvation** — Adding explicit water molecules around the solute.

**tleap** — AMBER's tool for building topologies.

**TIP3P** — 3-site rigid water model. Default in CasMD.

**Topology (top)** — File listing all atoms, bonds, charges, and force-field
parameters of a system.

**Trajectory (xtc)** — Sequence of atomic positions over simulation time.

**Verlet integrator** — Numerical scheme for stepping MD equations of motion.
Default in GROMACS.
