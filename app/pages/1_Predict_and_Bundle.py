"""Stage 1 — 5-card stepper: Sequences → Generate → Upload → Configure → Build."""
from __future__ import annotations
# Ensure repo root is on sys.path for `from app.shared import ...` when
# Streamlit loads this page file directly.
import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import io
import time
import tempfile
import zipfile

import streamlit as st

from app.shared import state
from app.shared.styles import inject_css
from app.shared.stepper import Stepper, render_chips, render_controls, advance
from app.shared.widgets import render_config_tabs

from hsingmd.predict.prep import prep_inputs, SERVER_URLS
from hsingmd.predict.boltz2 import parse_boltz2
from hsingmd.predict.protenix import parse_protenix
from hsingmd.predict.af3 import parse_af3
from hsingmd.predict.selector import rank, select_best
from hsingmd.build.pdb_prep import clean_pdb
from hsingmd.build.chains import detect_chains
from hsingmd.build.tleap_recipe import generate_tleap_input
from hsingmd.build.tleap_runner import run_tleap
from hsingmd.build.gromacs_convert import amber_to_gromacs
from hsingmd.bundle.packager import package_bundle


st.set_page_config(page_title="HsingMD — Predict & Bundle", page_icon="🧬",
                   layout="centered", initial_sidebar_state="collapsed")
inject_css()

# ---- Privacy gate ----
if not state.is_privacy_acked(st.session_state):
    st.warning("Please acknowledge the privacy disclaimer on the landing page first.")
    st.markdown("[← back to landing](/)")
    st.stop()

STEPPER = Stepper(titles=(
    "Sequences",
    "Predict",
    "Upload",
    "Configure",
    "Build",
))

if "current_step" not in st.session_state:
    st.session_state["current_step"] = 0
if state.JOB_NAME not in st.session_state:
    st.session_state[state.JOB_NAME] = state.default_job_name()

st.markdown(
    '<h1 style="text-align:center;margin-top:1rem">Stage 1 — Predict & Bundle</h1>',
    unsafe_allow_html=True,
)
render_chips(STEPPER)

step = st.session_state["current_step"]

# ============================================================
# Step 0 — Sequences
# ============================================================
if step == 0:
    with st.container(border=True):
        st.subheader("1. Sequences")
        st.caption("Provide your complex's sequences. Protein is required; RNA/DNA optional. "
                    "You can also upload a FASTA file to auto-fill the boxes below.")

        job_name = st.text_input("Job name", key=state.JOB_NAME)

        # FASTA file uploader — auto-populates the four sequence boxes below.
        fasta_upload = st.file_uploader(
            "Upload FASTA file (auto-detects protein / RNA / DNA)",
            type=["fasta", "fa", "faa", "fna", "txt"],
            key="fasta_upload",
        )
        if fasta_upload is not None:
            try:
                from app.shared.fasta import parse_fasta, fasta_to_form_fields
                text = fasta_upload.read().decode("utf-8", errors="replace")
                parsed = parse_fasta(text)
                fields = fasta_to_form_fields(parsed)
                # Populate session_state for the form fields BELOW
                if fields["protein_fasta"]:
                    st.session_state["protein_fasta"] = fields["protein_fasta"]
                if fields["rna_seq"]:
                    st.session_state["rna_seq"] = fields["rna_seq"]
                if fields["dna_seq"]:
                    st.session_state["dna_seq"] = fields["dna_seq"]
                if fields["target_seq"]:
                    st.session_state["target_seq"] = fields["target_seq"]
                counts = {k: len(v) for k, v in parsed.items()}
                summary = ", ".join(f"{n} {k}" for k, n in counts.items() if n > 0) or "no sequences"
                st.success(f"Parsed FASTA — found {summary}.")
            except Exception as e:
                st.error(f"Could not parse FASTA: {e}")
        protein_fasta = st.text_area("Protein FASTA", height=130, key="protein_fasta",
                                     placeholder=">protein\nMKVLW...")
        col1, col2, col3 = st.columns(3)
        with col1:
            rna_seq = st.text_input("RNA (5'→3')", key="rna_seq", placeholder="GCAU...")
        with col2:
            dna_seq = st.text_input("DNA (5'→3')", key="dna_seq", placeholder="ACGT...")
        with col3:
            target_seq = st.text_input("DNA target (5'→3')", key="target_seq",
                                        placeholder="ACGT...")

    can_advance = bool(st.session_state.get("protein_fasta", "").strip())
    render_controls(STEPPER, can_advance=can_advance, show_skip=True)
    if not can_advance:
        st.caption("Add a protein FASTA to continue.")

# ============================================================
# Step 1 — Generate submission files
# ============================================================
elif step == 1:
    with st.container(border=True):
        st.subheader("2. Generate submission files")
        st.caption(
            "HsingMD does not submit to the servers for you (their ToS preclude headless "
            "submission). It writes one input file per server below — paste those into the "
            "official UIs and download the result bundles. **Skip** if you already have "
            "downloaded bundles."
        )

        if st.button("Generate submission files", type="primary"):
            protein_fasta = st.session_state.get("protein_fasta", "")
            tmpdir = Path(tempfile.mkdtemp(prefix="hsingmd_prep_"))
            prep = prep_inputs(
                protein_fasta=protein_fasta,
                rna_sequence=st.session_state.get("rna_seq") or None,
                dna_sequence=st.session_state.get("dna_seq") or None,
                target_complement=st.session_state.get("target_seq") or None,
                output_dir=tmpdir,
                job_name=st.session_state[state.JOB_NAME],
            )
            st.session_state["_prep_files"] = {
                "boltz": str(prep.boltz_input),
                "protenix": str(prep.protenix_input),
                "af3": str(prep.af3_input),
            }
            st.success("Wrote 3 submission files.")

        prep_files = st.session_state.get("_prep_files")
        if prep_files:
            cols = st.columns(3)
            cols[0].download_button(
                "Boltz-2 input (.yaml)", Path(prep_files["boltz"]).read_bytes(),
                file_name="boltz_input.yaml")
            cols[1].download_button(
                "Protenix input (.json)", Path(prep_files["protenix"]).read_bytes(),
                file_name="protenix_input.json")
            cols[2].download_button(
                "AF3 input (.json)", Path(prep_files["af3"]).read_bytes(),
                file_name="af3_input.json")
            st.markdown("**Submit at:**")
            for k, url in SERVER_URLS.items():
                st.markdown(f"- {k}: [{url}]({url})")

    render_controls(STEPPER, can_advance=True, show_skip=True)

# ============================================================
# Step 2 — Upload prediction bundles
# ============================================================
elif step == 2:
    with st.container(border=True):
        st.subheader("3. Upload result bundles")
        st.caption(
            "Download the result bundle from each server, zip it if it's a folder, "
            "and upload here. One bundle is enough."
        )

        st.markdown("**Option A · Upload your own PDB**")
        own_pdb = st.file_uploader(
            "PDB file (skips prediction)", type=["pdb"], key="own_pdb",
        )
        if own_pdb is not None:
            import tempfile
            tmpdir = Path(tempfile.mkdtemp(prefix="hsingmd_own_pdb_"))
            saved = tmpdir / "input.pdb"
            saved.write_bytes(own_pdb.read())
            st.session_state[state.SELECTED_PDB] = str(saved)
            st.session_state["best_prediction"] = {
                "backend": "user-supplied",
                "model_id": 0,
                "iptm": None, "ptm": None, "plddt_mean": None,
            }
            st.success(f"Using your PDB: `{own_pdb.name}`")

        st.markdown("**Option B · Upload prediction bundles**")
        uploads = {
            "boltz": st.file_uploader("Boltz-2 bundle (.zip)", type="zip", key="up_boltz"),
            "protenix": st.file_uploader("Protenix bundle (.zip)", type="zip", key="up_protenix"),
            "af3": st.file_uploader("AlphaFold Server bundle (.zip)", type="zip", key="up_af3"),
        }

        def _extract_zip(upload, dest_root: Path, label: str) -> Path:
            target = dest_root / label
            target.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(upload.read())) as zf:
                zf.extractall(target)
            children = [p for p in target.iterdir() if not p.name.startswith(".")]
            if len(children) == 1 and children[0].is_dir():
                return children[0]
            return target

        bundles_chosen: list = []
        parsers = {"boltz": parse_boltz2, "protenix": parse_protenix, "af3": parse_af3}

        if any(uploads.values()):
            extract_root = Path(tempfile.mkdtemp(prefix="hsingmd_uploads_"))
            for label, upload in uploads.items():
                if upload is None:
                    continue
                try:
                    d = _extract_zip(upload, extract_root, label)
                    b = parsers[label](d)
                    bundles_chosen.append(b)
                    st.success(f"{label}: parsed {len(b.models)} models")
                except Exception as e:
                    st.error(f"{label}: parse failed — {e}")

        if bundles_chosen:
            st.markdown("**Models across uploaded backends:**")
            ranked = rank(bundles_chosen)
            rows = [
                {"Backend": m.backend, "Model": m.model_id, "Seed": m.seed,
                 "iPTM": f"{m.iptm:.3f}" if m.iptm else "--",
                 "pTM": f"{m.ptm:.3f}" if m.ptm else "--"}
                for m in ranked
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
            best = select_best(bundles_chosen)
            st.session_state[state.SELECTED_PDB] = str(best.pdb_path)
            st.session_state["best_prediction"] = {
                "backend": best.backend, "model_id": best.model_id,
                "iptm": best.iptm, "ptm": best.ptm, "plddt_mean": best.plddt_mean,
            }
            st.info(f"**Selected:** {best.backend} model {best.model_id} (iPTM={best.iptm:.3f}).")

    can_advance = state.SELECTED_PDB in st.session_state
    render_controls(STEPPER, can_advance=can_advance, show_skip=True)
    if not can_advance:
        st.caption("Upload at least one prediction bundle to continue.")

# ============================================================
# Step 3 — Configure
# ============================================================
elif step == 3:
    with st.container(border=True):
        st.subheader("4. Build configuration")
        st.caption(
            "Standard defaults match the validated protein–nucleic-acid protocol. Use Quick for the "
            "most common knobs, Advanced for SLURM and the rest."
        )
        build_config, bundle_spec = render_config_tabs(
            job_name=st.session_state[state.JOB_NAME])
        # Persist a serialized form so step 4 can use it without re-rendering tabs
        st.session_state["_build_config_box_padding_A"] = build_config.box_padding_A
        st.session_state["_bundle_spec_production_ns"] = bundle_spec.production_ns
    render_controls(STEPPER, can_advance=True, show_skip=True)

# ============================================================
# Step 4 — Build + Bundle (final step, action card)
# ============================================================
elif step == 4:
    from hsingmd.build.tleap_recipe import BuildConfig
    from hsingmd.bundle.spec import BundleSpec

    with st.container(border=True):
        st.subheader("5. Build + Bundle")

        job_name = st.session_state[state.JOB_NAME]
        selected = st.session_state.get(state.SELECTED_PDB)

        # Reuse the BuildConfig + BundleSpec produced by step 3
        build_config = BuildConfig(
            box_padding_A=float(st.session_state.get("_build_config_box_padding_A", 12.0))
        )
        bundle_spec = BundleSpec(
            job_name=job_name,
            production_ns=float(st.session_state.get("_bundle_spec_production_ns", 300.0)),
        )

        def _run_pipeline(input_pdb: Path, work_dir: Path, prefix: str) -> Path:
            progress = st.progress(0, text="Starting…")
            log = st.empty()
            t0 = time.time()
            def stamp() -> str: return f"{time.time() - t0:5.1f}s"

            log.code("Phase 1/4 · Preparing PDB (pdb4amber)…", language=None)
            cleaned = clean_pdb(input_pdb, work_dir / f"{prefix}_cleaned.pdb")
            progress.progress(25, text=f"[{stamp()}] PDB prep complete")

            log.code("Phase 2/4 · Detecting chains + building tleap recipe…", language=None)
            chains = detect_chains(cleaned)
            recipe = generate_tleap_input(str(cleaned.resolve()), prefix, chains, build_config)
            progress.progress(40, text=f"[{stamp()}] Recipe ready ({len(chains)} chains)")

            log.code("Phase 3/4 · Running tleap (AMBER topology + solvate + neutralize)…", language=None)
            prmtop, inpcrd = run_tleap(recipe, work_dir, output_prefix=prefix)
            progress.progress(70, text=f"[{stamp()}] tleap complete")

            log.code("Phase 4/4 · Converting AMBER → GROMACS + packaging zip…", language=None)
            amber_to_gromacs(prmtop, inpcrd, work_dir, prefix=prefix)
            out_zip = work_dir / f"{job_name}.zip"
            package_bundle(work_dir, bundle_spec, out_zip)
            progress.progress(100, text=f"[{stamp()}] ✅ Done — bundle ready")
            log.empty()
            return out_zip

        if not st.session_state.get(state.BUILD_DONE, False):
            if st.button("Build + Bundle", type="primary", disabled=not selected,
                          key="build_btn", use_container_width=True):
                try:
                    workdir = Path(tempfile.mkdtemp(prefix="hsingmd_build_"))
                    t_start = time.time()
                    out_zip = _run_pipeline(Path(selected), workdir, "system")
                    elapsed = time.time() - t_start
                    st.session_state[state.BUILD_DONE] = True
                    st.session_state[state.BUILD_OUTPUT_ZIP] = str(out_zip)
                    st.session_state[state.BUILD_ELAPSED_S] = elapsed
                    st.rerun()
                except Exception as e:
                    st.error(f"Build failed: {e}")
        else:
            elapsed = st.session_state[state.BUILD_ELAPSED_S]
            out_zip = Path(st.session_state[state.BUILD_OUTPUT_ZIP])
            size_mb = out_zip.stat().st_size / 1e6
            st.success(f"✅ Bundle ready — built in {elapsed:.1f}s ({size_mb:.1f} MB)")

            cols = st.columns([2, 1, 1])
            with cols[0]:
                with open(out_zip, "rb") as f:
                    st.download_button(
                        f"📦 Download {out_zip.name}", f.read(),
                        file_name=out_zip.name, type="primary",
                        use_container_width=True)
            with cols[1]:
                st.button("Build + Bundle", type="primary", disabled=True,
                          use_container_width=True, key="build_btn_done")
            with cols[2]:
                if st.button("↻ Reset", type="secondary", use_container_width=True,
                              key="reset_btn"):
                    state.reset_build(st.session_state)
                    st.session_state["current_step"] = 0
                    st.rerun()

    # Only show Back control on final step (no Next; the action button IS the action)
    cols = st.columns([1, 1, 1, 2])
    with cols[0]:
        if st.button("← Back", type="secondary", use_container_width=True, key="back_4"):
            st.session_state["current_step"] = 3
            st.rerun()
