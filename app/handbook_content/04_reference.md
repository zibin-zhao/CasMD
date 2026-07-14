# Reference and FAQ

## Accepted structure inputs

- PDB structure
- AlphaFold Server result archive
- Boltz-2 result archive
- Protenix result archive

Prediction archive uploads may be ZIP, 7Z, TAR, TAR.GZ, TGZ, or GZ when the
contained backend layout is recognized.

## Validated build settings

| Setting | Default / supported value |
|---|---|
| Protein force field | ff19SB |
| RNA force field | OL3 |
| DNA force field | bsc1 |
| Water | TIP3P |
| Box padding | 10–15 Å; 12 Å default |
| Salt | neutralize only or 0.15 M NaCl |
| Temperature | 280–320 K; 310.15 K default |
| Production | 10–5000 ns; 500 ns default |

Automated pH-dependent protonation is not supported. Protonation states are
read from the uploaded structure.

## Analysis archive

The active dashboard recognizes:

- `results.json`
- `rmsd.dat`
- `rmsf.dat`
- `rg.dat`
- optional `rmsd.png`, `rmsf.png`, and `rg.png`

Guided engineering additionally uses:

- `topology_index.json` — protein/nucleic residue blocks and selection hints
- `engineering_config.json` — functional regions, objectives, constraints, and truncations
- `engineering.json` — dynamic residue/nucleotide fingerprints generated beside the trajectory
- guided design ZIP — fingerprints, candidates, selected set, rationale, and provenance

The downloaded StrandMD analysis package contains:

- `manifest.json`
- one summary JSON per run
- numerical plot data
- available figures
- `comparison_summary.json` for two-run comparisons
- optional `project.json` with project, condition, and replicate metadata
- `README.md` with interpretation limits

DOCX and PPTX generation is not part of the active web workflow.

## Frequently asked questions

### Can I upload an experimental structure?

Yes. Upload a PDB on the structure-upload step and skip prediction.

### Can I simulate a phosphorylated or modified residue?

Not through the validated workflow. Custom parameterization is required and
must be reviewed outside StrandMD.

### Can I use a different force field or water model?

Not from the active validated UI. Alternative choices were removed until each
combination has end-to-end build and reference-system validation.

### Why does the public Space not run 500 ns for me?

Production MD is too compute-intensive for a shared CPU Space. StrandMD creates
a portable bundle for your own local GPU or HPC allocation.

### Why are there no p-values for two trajectories?

MD frames are autocorrelated and are not independent replicates. Two runs can be
compared descriptively, but statistical inference requires independently
initialized replicate simulations for every condition.

### Does a high mutation score predict activity?

No. It means that, under the supplied trajectory and selections, the residue
has strong engagement with a `weaken` region and relatively little configured
preservation or structural-risk burden. Expression, folding, binding, and
activity must be tested experimentally.

### How should I compare a truncation?

Use sequence- or residue-identity-aware mapping. Do not align RMSF profiles by
array index after deleting or inserting residues.

### Is the Variant A tutorial evidence for a real protein design?

No. Variant A is fictional and its values are synthetic. A real candidate
requires independent simulations plus wet-lab protein-quality, binding, and
activity measurements.

### Can I run StrandMD locally?

Yes. The public product name is StrandMD, while the current repository, Python
package, Docker image, and CLI retain the internal `casmd` name during
migration.

## Citation status

StrandMD is currently an unpublished online toolkit. Cite the underlying
prediction, force-field, simulation, and analysis tools listed on the
Acknowledgements page. A stable StrandMD software citation will be assigned
when the publication and release repository are finalized.
