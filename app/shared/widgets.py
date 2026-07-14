"""Reusable widgets for the validated StrandMD preparation protocol."""
from __future__ import annotations
import streamlit as st

from casmd.build.tleap_recipe import BuildConfig
from casmd.bundle.spec import BundleSpec


_ION_PAIRS = {
    "Na⁺ / Cl⁻": ("Na+", "Cl-"),
    "K⁺ / Cl⁻": ("K+", "Cl-"),
    "Mg²⁺ / Cl⁻": ("Mg2+", "Cl-"),
}

_SALT_LABELS = {
    "0 M (neutralize only)": 0.0,
    "0.05 M": 0.05,
    "0.15 M (physiological)": 0.15,
}


def _resolve_ion_pair(label: str, *, custom_cation: str = "Na+",
                      custom_anion: str = "Cl-") -> tuple[str, str]:
    """Map an ion-pair dropdown label to (cation, anion) AMBER names."""
    if label == "Custom":
        return (custom_cation, custom_anion)
    return _ION_PAIRS.get(label, ("Na+", "Cl-"))


def _salt_molarity_from_label(label: str, *, custom: float) -> float:
    """Map a salt-concentration label to molarity. 'Custom' uses the input."""
    if label == "Custom":
        return float(custom)
    return _SALT_LABELS.get(label, 0.0)


def build_default_config() -> BuildConfig:
    return BuildConfig()


def default_bundle_spec(*, job_name: str) -> BundleSpec:
    return BundleSpec(job_name=job_name)


def render_config_tabs(*, job_name: str) -> tuple[BuildConfig, BundleSpec]:
    """Render validated protocol and HPC settings.

    Only options that are carried into the generated files are shown.  The
    force-field combination is intentionally fixed until alternatives have
    their own end-to-end validation fixtures.
    """
    tab_protocol, tab_hpc = st.tabs(["Validated protocol", "HPC settings"])

    with tab_protocol:
        st.info(
            "Validated scope: protein-DNA, protein-RNA, and protein-DNA-RNA "
            "complexes using ff19SB + OL3 + bsc1 + TIP3P."
        )
        ff_cols = st.columns(4)
        for col, value, label in zip(
            ff_cols,
            ("ff19SB", "OL3", "bsc1", "TIP3P"),
            ("Protein", "RNA", "DNA", "Water"),
        ):
            col.metric(label, value)

        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Temperature (K)", 280.0, 320.0, 310.15,
                step=0.05, key="std_temp",
            )
            st.slider(
                "Box padding (Å)", 10.0, 15.0, 12.0,
                step=0.5, key="std_box",
            )
            st.selectbox(
                "NaCl concentration",
                ["0 M (neutralize only)", "0.15 M"],
                0, key="std_salt_label",
            )
        with col2:
            st.number_input(
                "Production length (ns)", 10.0, 5000.0, 500.0,
                step=10.0, key="std_prod_ns",
            )
            st.number_input(
                "NVT length (ps)", 50.0, 5000.0, 500.0,
                key="std_nvt_ps",
            )
            st.number_input(
                "NPT length (ps)", 50.0, 5000.0, 500.0,
                key="std_npt_ps",
            )
            st.number_input(
                "Trajectory output interval (ps)", 10.0, 1000.0, 100.0,
                step=10.0, key="std_output_ps",
            )
        st.caption(
            "Protonation states are read from the uploaded structure. "
            "Automated pH-dependent protonation is not yet supported."
        )

    with tab_hpc:
        st.text_input("SLURM account", "hsinglab", key="adv_account")
        st.text_input("SLURM partition", "gpu-l20", key="adv_partition")
        st.text_input("gpus-per-node", "l20:4", key="adv_gpus")
        st.number_input("CPUs per task", 1, 256, 64, key="adv_cpus")
        st.number_input("Time limit (hours)", 1, 240, 72, key="adv_time")
        st.text_input("Notification email (optional)", key="adv_email")
        st.text_input("GROMACS binary", "gmx_mpi", key="adv_gmx")

    salt_molarity = _salt_molarity_from_label(
        st.session_state.get("std_salt_label", "0 M (neutralize only)"),
        custom=0.15,
    )
    build_config = BuildConfig(
        protein_ff="ff19SB",
        rna_ff="OL3",
        dna_ff="bsc1",
        water_ff="tip3p",
        box_padding_A=float(st.session_state.get("std_box", 12.0)),
        ion_cation="Na+",
        ion_anion="Cl-",
        salt_molarity=salt_molarity,
    )
    bundle_spec = BundleSpec(
        production_ns=float(st.session_state.get("std_prod_ns", 500.0)),
        nvt_ps=float(st.session_state.get("std_nvt_ps", 500.0)),
        npt_ps=float(st.session_state.get("std_npt_ps", 500.0)),
        temperature_K=float(st.session_state.get("std_temp", 310.15)),
        output_every_ps=float(st.session_state.get("std_output_ps", 100.0)),
        job_name=job_name,
        account=st.session_state.get("adv_account", "hsinglab"),
        partition=st.session_state.get("adv_partition", "gpu-l20"),
        gpus_per_node=st.session_state.get("adv_gpus", "l20:4"),
        cpus_per_task=int(st.session_state.get("adv_cpus", 64)),
        time_hours=int(st.session_state.get("adv_time", 72)),
        email=st.session_state.get("adv_email") or None,
        gmx_binary=st.session_state.get("adv_gmx", "gmx_mpi"),
    )
    return build_config, bundle_spec
