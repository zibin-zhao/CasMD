# Stage 1 walkthrough — Predict and Bundle

Stage 1 is a 5-card stepper. You move through one card at a time.

## Step 1 — Sequences

Either upload a FASTA file (auto-detects protein / RNA / DNA) or paste the
sequences manually. Only the protein is required; RNA and DNA are optional.

## Step 2 — Predict (skippable)

CasMD doesn't predict structures itself — instead it formats your sequences
into a submission file for each of three online services. Submit at the
official URL of each service, download the bundle, and proceed.

If you already have prediction bundles or a PDB, click **Skip**.

## Step 3 — Upload bundles

Upload the downloaded zip from any one (or all) of:
- Boltz-2 (Tamarind or similar)
- Protenix (bioos.com)
- AlphaFold Server

Or upload your own PDB directly. CasMD parses the bundles, shows iPTM/pTM
scores across all backends, and picks the highest-iPTM model as your input.

## Step 4 — Configure (skippable)

Choose Quick / Standard / Advanced tabs to set MD parameters. Standard is
the recommended default (matches the validated protocol — see "Why these
defaults").

## Step 5 — Build + Bundle

Click **Build + Bundle**. CasMD runs pdb4amber → tleap → parmed in about
30 seconds, packages everything as a `<job_name>.zip`, and gives you a
Download button. Take that zip to your HPC.
