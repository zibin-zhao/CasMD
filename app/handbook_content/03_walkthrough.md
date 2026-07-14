# Workflow walkthrough

## Define a guided-engineering objective

Open **Engineer → Define objective**. Enter an MDAnalysis protein selection and
one or more nucleic-acid regions. Assign every region an objective:

- `weaken` for an unwanted target interface;
- `preserve` for desired engagement such as a spacer or target duplex; or
- `monitor` for descriptive reporting only.

If selection identifiers are uncertain, run the ordinary bundled analysis
first and upload `topology_index.json`. It lists the protein and nucleic residue
blocks and gives starting selection expressions.

Download `engineering_config.json`. Protected residues and optional structural
risk penalties constrain the mutation ranking. A proposed truncation range can
be included for interface-coverage auditing.

## Prepare a simulation

### 1. Sequences

Enter a project-safe job name and provide a protein FASTA. DNA and RNA inputs
are optional. Multi-record FASTA uploads can populate the sequence fields.

### 2. Predict

StrandMD creates input files for AlphaFold Server, Boltz-2, and Protenix. Submit
them through the official services and download the returned result bundles.
StrandMD does not submit private sequences to third-party prediction servers.

Skip this step if you already have a prediction result or experimental model.

### 3. Upload

Upload one or more prediction archives, or provide a PDB directly. StrandMD
parses compatible results and selects the highest-ranked model when prediction
confidence is available.

Before publication use, inspect chain identity, residue numbering, missing
atoms, unsupported residues, and termini.

### 4. Configure

The validated protocol tab shows the effective protein, RNA, DNA, and water
models plus temperature, box padding, salt, equilibration, production length,
and output interval.

The HPC tab controls SLURM account, partition, GPU request, CPU count, time
limit, notification email, and GROMACS binary. Every displayed control is
written into the generated output.

### 5. Build and download

Review the complete protocol summary, then build the solvated system and HPC
package. Salt addition uses a two-pass build so requested concentration is
calculated from the solvated water count.

The resulting ZIP includes topology, coordinates, MDP files, SLURM script,
analysis script, and run instructions.

## Run on your compute

Extract the bundle on a workstation or HPC system. Follow the included README
and SLURM script. Long production MD should run on compute you control, not the
public web application.

The internal command/package name remains `casmd` during the StrandMD product
rename, so existing Docker and CLI commands continue to work.

## Analyze a trajectory

Run the bundled analysis script beside the completed trajectory. It produces a
small archive containing `results.json`, numerical `.dat` files, and available
figures.

For guided engineering, rerun with the objective file:

```bash
python analyze.py --top md_solute.gro --xtc md.xtc -o analysis/ \
  --engineering-config engineering_config.json --source-label "WT replicate 1"
```

Upload `analysis/engineering.json` on **Engineer → Rank a trajectory**. The
dashboard reports dynamic residue/nucleotide occupancy, RNA 2′-oxygen proximity,
contact events and lifetimes, mutation-score components, complementary interface
coverage, and the truncation audit.

Upload that archive on **Analyze & Compare**. The single-run dashboard shows:

- frame count and declared equilibration discard;
- equilibrium protein RMSD;
- protein RMSF;
- equilibrium radius of gyration; and
- interactive time-series or residue plots.

Download the complete analysis package. It contains summary JSON, plot data,
figures, version provenance, and interpretation limits.

## Compare two runs

Add a second archive and provide meaningful condition labels. The current
two-run view is descriptive:

- equilibrium regions are removed before time-series comparison;
- unequal physical time axes are interpolated only within their shared range;
- RMSF overlay is blocked until equivalent residue identity/numbering is
  confirmed; and
- frame-wise significance values are not shown.

For truncations or insertions, wait for or provide a gap-aware residue map.
For inferential analysis, organize several independent replicates under every
condition and compare replicate-level summaries.

For engineering objectives, upload baseline and variant `engineering.json`
files on **Engineer → Compare a variant**. Region interaction mass is compared
according to its `weaken`, `preserve`, or `monitor` objective.

## Explore the fictional Variant A tutorial

Open **Examples → Variant A tutorial** to see how a reference, controls, and an
optimization candidate can be represented. The page uses invented residue
numbering and synthetic measurements, and separates simulation trends from the
experimental validation a real project would require.
