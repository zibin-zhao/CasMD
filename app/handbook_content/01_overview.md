# StrandMD overview

StrandMD is a web-guided workflow for molecular dynamics of
protein–nucleic-acid complexes.

> **Define the objective. Run anywhere. Engineer from the trajectory.**

Long production simulations do not run on the public Hugging Face Space.
StrandMD prepares a portable GROMACS package, you run it on local or HPC
compute, and then upload the lightweight analysis archive.

## Intended users

StrandMD is designed for wet-lab researchers who have a new protein, DNA, or
RNA complex and need an interpretable MD workflow without becoming GROMACS
specialists.

Typical questions include:

- Does a protein variant remain globally stable?
- Does a truncation change flexibility near an interface?
- Are guide, target, duplex, or handle contacts preserved?
- Which variants should move forward to binding or activity experiments?

MD supports hypothesis generation. It does not prove affinity, catalytic
activity, or biological function.

## Validated system scope

- Protein + DNA
- Protein + RNA
- Protein + DNA + RNA ternary complexes
- Point mutants, multi-site mutants, linkers, and truncations built from
  standard residues

The current validated protocol uses ff19SB for protein, OL3 for RNA, bsc1 for
DNA, TIP3P water, a rectangular solvent box, and NaCl or neutralization-only
ions.

## Not yet supported

- Membranes
- Covalent ligands
- Nonstandard residues and post-translational modifications
- Custom metal centers
- Automated pH-dependent protonation
- Modified nucleic-acid termini requiring custom parameters

## Four workflows

### Engineer

Define nucleic-acid regions to weaken, preserve, or monitor. Download an
`engineering_config.json`, run the portable contact analysis beside the
trajectory, then upload `engineering.json` to rank mutations, select a
complementary mutation set, and audit proposed truncations.

### Prepare

Provide sequences, obtain a structure-prediction result or upload a PDB, review
the validated protocol and HPC settings, then download a portable bundle.

### Analyze & Compare

Run the included `analyze.py` beside the completed trajectory. Upload its small
archive to explore global metrics and download a provenance-rich analysis ZIP.
Two uploaded runs can be compared descriptively. Inferential statistics require
independent simulation replicates.

### Examples

The fully fictional **Variant A** tutorial demonstrates how to organize an
interface-engineering question, controls, synthetic MD evidence, and explicit
evidence limitations. Its construct names, residue numbers, and values are
invented and are not derived from an unpublished project.

## Privacy

Do not upload unpublished or proprietary sequences to the public Space. Run the
same application locally for sensitive projects.
