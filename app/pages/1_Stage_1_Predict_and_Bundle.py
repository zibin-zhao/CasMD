"""Stage 1 — 5-card stepper: Sequences → Generate → Upload → Configure → Build."""
from __future__ import annotations
# Ensure repo root is on sys.path for `from app.shared import ...` when
# Streamlit loads this page file directly.
import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import time
import tempfile
import zipfile
from dataclasses import asdict

import streamlit as st

from app.shared import state
from app.shared.styles import inject_css
from app.shared.stepper import Stepper, render_chips, render_controls
from app.shared.widgets import render_config_tabs

from casmd.predict.prep import prep_inputs, SERVER_URLS
from casmd.predict.boltz2 import parse_boltz2
from casmd.predict.protenix import parse_protenix
from casmd.predict.af3 import parse_af3
from casmd.predict.selector import rank, select_best
from casmd.build.system import build_system
from casmd.bundle.packager import package_bundle


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
    '<h1 style="text-align:center;margin-top:1rem">Prepare a simulation</h1>',
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
            "StrandMD does not submit to the servers for you (their ToS preclude headless "
            "submission). It writes one input file per server below — paste those into the "
            "official UIs and download the result bundles. **Skip** if you already have "
            "downloaded bundles."
        )

        if st.button("Generate submission files", type="primary"):
            protein_fasta = st.session_state.get("protein_fasta", "")
            tmpdir = Path(tempfile.mkdtemp(prefix="casmd_prep_"))
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
            tmpdir = Path(tempfile.mkdtemp(prefix="casmd_own_pdb_"))
            saved = tmpdir / "input.pdb"
            saved.write_bytes(own_pdb.read())
            st.session_state[state.SELECTED_PDB] = str(saved)
            st.session_state["best_prediction"] = {
                "backend": "user-supplied",
                "model_id": 0,
                "iptm": None, "ptm": None, "plddt_mean": None,
            }
            st.success(f"Using your PDB: `{own_pdb.name}`")

        st.markdown("**Option B · Upload prediction bundles** (.zip, .7z, .tar.gz)")
        from app.shared.archive import SUPPORTED_UPLOAD_TYPES, extract_archive
        uploads = {
            "boltz": st.file_uploader("Boltz-2 bundle", type=SUPPORTED_UPLOAD_TYPES, key="up_boltz"),
            "protenix": st.file_uploader("Protenix bundle", type=SUPPORTED_UPLOAD_TYPES, key="up_protenix"),
            "af3": st.file_uploader("AlphaFold Server bundle", type=SUPPORTED_UPLOAD_TYPES, key="up_af3"),
        }

        def _extract_zip(upload, dest_root: Path, label: str) -> Path:
            target = dest_root / label
            target.mkdir(parents=True, exist_ok=True)
            extract_archive(upload.read(), target, upload.name)
            children = [p for p in target.iterdir() if not p.name.startswith(".")]
            if len(children) == 1 and children[0].is_dir():
                return children[0]
            return target

        bundles_chosen: list = []
        parsers = {"boltz": parse_boltz2, "protenix": parse_protenix, "af3": parse_af3}

        if any(uploads.values()):
            extract_root = Path(tempfile.mkdtemp(prefix="casmd_uploads_"))
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
            st.dataframe(rows, width="stretch", hide_index=True)
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
        st.caption("Choose the validated molecular protocol and your HPC settings.")
        build_config, bundle_spec = render_config_tabs(
            job_name=st.session_state[state.JOB_NAME])
        # Persist every effective field so the review/build step cannot silently
        # fall back to defaults.
        st.session_state[state.BUILD_CONFIG] = asdict(build_config)
        st.session_state[state.BUNDLE_SPEC] = asdict(bundle_spec)
    render_controls(STEPPER, can_advance=True, show_skip=True)

# ============================================================
# Step 4 — Build + Bundle (final step, action card)
# ============================================================
elif step == 4:
    from casmd.build.tleap_recipe import BuildConfig
    from casmd.bundle.spec import BundleSpec

    with st.container(border=True):
        st.subheader("5. Build + Bundle")

        job_name = st.session_state[state.JOB_NAME]
        selected = st.session_state.get(state.SELECTED_PDB)

        # Reuse the complete configurations produced by step 3. Direct jumps to
        # this step (including AppTest) still receive honest validated defaults.
        build_values = st.session_state.get(state.BUILD_CONFIG, {})
        bundle_values = st.session_state.get(state.BUNDLE_SPEC, {})
        build_config = BuildConfig(**build_values)
        bundle_spec = BundleSpec(job_name=job_name, **{
            key: value for key, value in bundle_values.items() if key != "job_name"
        })

        st.markdown("**Protocol review**")
        review_cols = st.columns(3)
        review_cols[0].markdown(
            "**Force fields**  \nff19SB / OL3 / bsc1  \nTIP3P water"
        )
        review_cols[1].markdown(
            f"**Environment**  \n{bundle_spec.temperature_K:g} K  \n"
            f"{build_config.salt_molarity:g} M NaCl  \n"
            f"{build_config.box_padding_A:g} Å padding"
        )
        review_cols[2].markdown(
            f"**Run**  \n{bundle_spec.production_ns:g} ns production  \n"
            f"{bundle_spec.output_every_ps:g} ps output  \n"
            f"{bundle_spec.partition} / {bundle_spec.gpus_per_node}"
        )

        if not st.session_state.get(state.BUILD_DONE, False):
            if st.button("Build + Bundle", type="primary", disabled=not selected,
                          key="build_btn", width="stretch"):
                from app.shared.errors import friendly_error
                with st.status("Building system + bundle...", expanded=True) as status:
                    try:
                        workdir = Path(tempfile.mkdtemp(prefix="casmd_build_"))
                        prefix = "system"
                        input_pdb = Path(selected)
                        t_start = time.time()

                        st.write(
                            "• Cleaning, typing, solvating, adding ions, and "
                            "converting to GROMACS..."
                        )
                        build_system(input_pdb, workdir, build_config, prefix=prefix)

                        st.write("• Templating MDPs + SLURM + `analyze.py` — zipping bundle...")
                        out_zip = workdir / f"{job_name}.zip"
                        package_bundle(workdir, bundle_spec, out_zip)

                        elapsed = time.time() - t_start
                        st.session_state[state.BUILD_DONE] = True
                        st.session_state[state.BUILD_OUTPUT_ZIP] = str(out_zip)
                        st.session_state[state.BUILD_ELAPSED_S] = elapsed
                        status.update(label="✓ Build complete", state="complete", expanded=False)
                        st.rerun()
                    except Exception as exc:
                        status.update(label="✗ Build failed", state="error", expanded=True)
                        st.error(friendly_error(exc, context="build"))
                        st.stop()
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
                        width="stretch")
            with cols[1]:
                st.button("Build + Bundle", type="primary", disabled=True,
                          width="stretch", key="build_btn_done")
            with cols[2]:
                if st.button("↻ Reset", type="secondary", width="stretch",
                              key="reset_btn"):
                    state.reset_build(st.session_state)
                    st.session_state["current_step"] = 0
                    st.rerun()

            # Run-time estimate on THIS hardware — shown everywhere, including
            # the CPU-only hosted Space (which lacks the run panel), so users
            # see what a real run would cost before choosing local vs HPC.
            from casmd.run.gpu_check import detect_gpu, format_eta
            _hw = detect_gpu()
            _prod_ns = bundle_spec.production_ns
            _hours = _prod_ns * 24 / max(_hw.est_ns_per_day, 0.1)
            if _hw.kind in ("cpu", "apple"):
                st.warning(
                    f"⏱️ **Estimated run time:** {_prod_ns:g} ns ≈ **{format_eta(_hours)}** "
                    f"on **{_hw.name}** (~{_hw.est_ns_per_day:g} ns/day, CPU-only). "
                    "This hosted Space has no GPU — practical only for a quick look. "
                    "For a full run, use a local GPU (the `casmd-full` Docker image) "
                    "or the **Download bundle** above on an HPC cluster."
                )
            else:
                st.info(
                    f"⏱️ **Estimated run time:** {_prod_ns:g} ns ≈ **{format_eta(_hours)}** "
                    f"on **{_hw.name}** (~{_hw.est_ns_per_day:g} ns/day)."
                )

            # Optional measured benchmark (guardrailed: gmx-only, 1 run/session).
            from app.shared.cpu_bench import render_cpu_benchmark
            render_cpu_benchmark(out_zip=out_zip, production_ns=_prod_ns)

            # Local-run panel — only shown inside the casmd-full image.
            from app.shared.local_run import is_local_run_enabled, render_local_run_panel
            if is_local_run_enabled():
                run_dir = Path(tempfile.mkdtemp(prefix="casmd_local_run_"))
                with zipfile.ZipFile(out_zip) as zf:
                    zf.extractall(run_dir)
                # If the zip wraps everything in a top-level dir, descend into it
                children = [p for p in run_dir.iterdir() if p.is_dir()]
                if len(children) == 1:
                    run_dir = children[0]
                st.markdown("---")
                render_local_run_panel(bundle_dir=run_dir, default_ns=50.0)

    # Only show Back control on final step (no Next; the action button IS the action)
    cols = st.columns([1, 1, 1, 2])
    with cols[0]:
        if st.button("← Back", type="secondary", width="stretch", key="back_4"):
            st.session_state["current_step"] = 3
            st.rerun()

from app.shared.footer import render_footer
render_footer()
