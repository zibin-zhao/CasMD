"""About · Acknowledgements & citations."""
import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from app.shared.styles import inject_css
from casmd import __version__

inject_css()


CITATIONS = [
    ("Structure prediction", [
        ("AlphaFold 3", "Abramson, J. et al. (2024). Accurate structure prediction of biomolecular interactions with AlphaFold 3. *Nature*, 630, 493–500."),
        ("Boltz-2",     "Wohlwend, J. et al. (2024). Boltz-1: democratizing biomolecular interaction modeling. *bioRxiv*."),
        ("Protenix",    "ByteDance Research (2024). Protenix: an open-source biomolecular structure prediction model."),
    ]),
    ("System building", [
        ("AmberTools",  "Case, D.A. et al. (2024). AmberTools 24. *J. Chem. Inf. Model.*, 64, 6183–6191."),
        ("ff19SB",      "Tian, C. et al. (2020). ff19SB: amino-acid-specific protein backbone parameters trained against quantum mechanics energy surfaces in solution. *JCTC*, 16, 528–552."),
        ("OL3",         "Zgarbová, M. et al. (2011). Refinement of the Cornell et al. nucleic acids force field based on reference quantum chemical calculations of glycosidic torsion profiles. *JCTC*, 7, 2886–2902."),
        ("BSC1",        "Ivani, I. et al. (2016). Parmbsc1: a refined force field for DNA simulations. *Nat. Methods*, 13, 55–58."),
    ]),
    ("Simulation", [
        ("GROMACS",     "Abraham, M.J. et al. (2015). GROMACS: high performance molecular simulations through multi-level parallelism from laptops to supercomputers. *SoftwareX*, 1–2, 19–25."),
        ("GROMACS 2024","Páll, S. et al. (2020). Heterogeneous parallelization and acceleration of molecular dynamics simulations in GROMACS. *JCP*, 153, 134110."),
    ]),
    ("Analysis", [
        ("MDAnalysis",  "Michaud-Agrawal, N. et al. (2011). MDAnalysis: a toolkit for the analysis of molecular dynamics simulations. *JCC*, 32, 2319–2327."),
        ("ParmEd",      "Shirts, M.R. et al. (2017). Lessons learned from comparing molecular dynamics engines on the SAMPL5 dataset. *JCAMD*, 31, 147–161."),
    ]),
]


st.title("Acknowledgements")
st.caption("If you publish work generated with StrandMD, please cite the underlying tools below.")

# §A — Citations for dependencies
st.header("📚 Citations for dependencies")
for section, items in CITATIONS:
    with st.container(border=True):
        st.subheader(section)
        for tool, ref in items:
            st.markdown(f"**{tool}** — {ref}")

# §B — How to cite StrandMD
st.header("📝 How to cite StrandMD itself")
st.info("StrandMD is currently an **unpublished online toolkit** — no DOI, no peer review yet. Please cite as an online resource:")

with st.container(border=True):
    st.subheader("Plain text")
    st.code(
        "Zhao, Z., & Hsing, I.-M. (2026). StrandMD: a web workflow for "
        "protein–nucleic acid molecular dynamics simulation. Hsing Lab, "
        "Department of Chemical and Biological Engineering, HKUST. "
        "Unpublished. https://github.com/zibin-zhao/CasMD · "
        f"https://huggingface.co/spaces/zzhaobz/HsingMD Version {__version__}.",
        language="text",
    )

with st.container(border=True):
    st.subheader("BibTeX")
    st.code(
        '@misc{zhao2026strandmd,\n'
        '  author       = {Zhao, Zibin and Hsing, I-Ming},\n'
        '  title        = {StrandMD: a web workflow for protein--nucleic acid '
        'molecular dynamics simulation},\n'
        '  year         = {2026},\n'
        '  howpublished = {Online toolkit, Hsing Lab, HKUST},\n'
        f'  note         = {{Unpublished. Version {__version__}.}},\n'
        '  url          = {https://huggingface.co/spaces/zzhaobz/HsingMD}\n'
        '}',
        language="bibtex",
    )

# §C — Lab and author credits
st.header("🏛 Lab and author credits")
with st.container(border=True):
    lab_logo = _REPO_ROOT / "app" / "assets" / "logo-hsing-group.png"
    cols = st.columns([1, 4])
    with cols[0]:
        if lab_logo.exists():
            st.image(str(lab_logo), width=120)
    with cols[1]:
        st.markdown(
            "### Hsing Lab, HKUST\n"
            "Department of Chemical and Biological Engineering · "
            "The Hong Kong University of Science and Technology.\n\n"
            "**PI** — Prof. I-Ming Hsing.  \n"
            "**Author / maintainer** — Zibin Zhao (`zzhaobz@connect.ust.hk`)."
        )

from app.shared.footer import render_footer
render_footer()
