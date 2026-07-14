---
title: StrandMD
emoji: 🧬
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8501
pinned: false
license: mit
short_description: Guided MD for protein–nucleic-acid engineering
---

# StrandMD

StrandMD is a guided molecular-dynamics workflow for protein–DNA, protein–RNA,
and protein–DNA–RNA complexes. It helps researchers define an interface objective,
prepare a portable simulation bundle, analyze trajectories, and turn dynamic
contacts into auditable mutation or truncation hypotheses.

## Public tutorial

The bundled **Variant A** example is completely fictional. Construct names,
residue numbering, simulation values, and outcomes are invented and are not
derived from an unpublished project.

Real sequences, structures, trajectories, and case-study notes must remain local
under `private_case_studies/`, which is excluded from Git and Docker contexts.

## Use StrandMD

1. **Public web app:** [StrandMD on Hugging Face Spaces](https://huggingface.co/spaces/zzhaobz/HsingMD)
2. **Local Docker:** `docker build -t strandmd . && docker run -p 8501:8501 strandmd`
3. **Local Python:** `pip install -e .` and run `casmd-ui`

Use a local installation for unpublished or proprietary sequences. The public
Space is intended for synthetic, published, or otherwise non-sensitive inputs.

## Workflow

- **Engineer:** define regions to weaken, preserve, or monitor; rank mutation
  candidates; audit truncations; compare variants.
- **Prepare:** ingest a predicted structure or PDB and create a portable GROMACS
  package for local or HPC execution.
- **Analyze & Compare:** visualize global and residue-level metrics and download
  a provenance-rich analysis package.

Long production simulations do not run on the shared public Space.

## Development

```bash
PYTHONPATH=src:. pytest -q
python -m streamlit run app/streamlit_app.py
```

The public test suite uses synthetic data. Private validation fixtures are not
part of the repository or deployment.

## Evidence limits

Single trajectories are descriptive and their frames are autocorrelated.
Replicate-level inference requires independently initialized simulations for
each condition. Mutation rankings do not predict expression, folding, binding,
activity, or selectivity; experimental validation remains essential.

## Citation status

StrandMD is currently an unpublished toolkit. A stable software citation and the
real case study will be released after the corresponding manuscript or preprint
is ready. Until then, cite the underlying methods listed in the in-app
Acknowledgements page.

## License

MIT — see [LICENSE](LICENSE).
