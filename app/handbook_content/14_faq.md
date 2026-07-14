# Frequently Asked Questions

## How long does a 500 ns run take?

Depends on system size and your GPU. On HKUST's `gpu-l20` partition, a 50k-atom
solvated tri-complex finishes 500 ns in roughly 24-36 hours on 4× L20 GPUs.

## Why does iPTM matter?

iPTM is the confidence score for the **interface** between two predicted
chains. For a protein–nucleic acid complex, a high iPTM (>0.8) means the
predictor is confident in how the protein and the nucleic acid are arranged
relative to each other.

## Can I use my own PDB?

Yes. On Stage 1 step 3 (Upload), choose "Option A — Upload your own PDB"
instead of uploading prediction bundles. CasMD will skip prediction and
go straight to building.

## My sequence has phosphorylation. Will CasMD handle it?

Not yet — phosphorylated residues require special force-field parameters
that CasMD doesn't ship in v0.7. This is on the Phase 2 roadmap.

## Why does the build fail with "addIons2 hangs"?

This was a bug in early versions; the current pipeline uses `addIonsRand`
which finishes in seconds. Upgrade to v0.7+.

## Can I run CasMD locally?

Yes. Either pull the Docker image (`docker run -p 8501:8501 casmd`) or
install with `pip install -e .` and run `casmd-ui`.

## Where does my data go?

If you use the HuggingFace Space, sequences and intermediate files transit
public cloud. For sensitive sequences, run locally via Docker. See the
privacy disclaimer on the homepage.

## What if I get different iPTM scores across backends?

That's normal — the three backends use different model architectures and
training data. CasMD shows all of them and picks the highest-iPTM by default,
but you can override.

## Can I edit the MDP files in the bundle?

Yes, freely. The bundle is just a zip — you can swap parameters before
submitting on your HPC.

## How do I cite CasMD?

See the Acknowledgements page. Short answer: cite the GitHub repo + version,
plus the underlying tools (AlphaFold 3 paper, GROMACS paper, etc.).
