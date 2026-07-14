"""Trajectory-guided mutation and truncation design workflow."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import plotly.graph_objects as go
import streamlit as st

from app.shared.engineering_examples import load_synthetic_engineering_tutorial
from app.shared.footer import render_footer
from app.shared.styles import inject_css
from casmd.engineering.design import compare_variants
from casmd.engineering.export import build_design_package
from casmd.engineering.io import load_design_report
from casmd.engineering.models import (
    EngineeringConfig,
    RegionObjective,
    RegionSpec,
    TruncationSpec,
)


inject_css()

st.caption("GUIDED ENGINEERING · EVIDENCE, NOT ACTIVITY PREDICTION")
st.title("Engineer a protein–nucleic-acid interface")
st.markdown(
    "Define what to weaken and what to preserve, calculate a dynamic interaction "
    "fingerprint beside the trajectory, then rank complementary mutations and "
    "audit proposed truncations."
)
st.warning(
    "Uploaded fingerprints may reveal unpublished residue-level results. Use a "
    "local StrandMD instance for sensitive projects. Mutation rankings require "
    "independent simulation replicates and experimental validation."
)


def _records(value):
    if hasattr(value, "to_dict"):
        return value.to_dict("records")
    return list(value)


def _parse_risks(text: str) -> dict[str, float]:
    output = {}
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        token, risk = item.split("=", 1)
        output[token.strip()] = float(risk)
    return output


def _render_report(report) -> None:
    if report.provenance.get("data_status") == "fictional_synthetic_tutorial":
        st.info(
            "Fictional tutorial: construct names, residue numbering, and values are "
            "invented and are not derived from an unpublished project."
        )

    overview = st.columns(4)
    overview[0].metric("Analyzed frames", f"{report.n_frames:,}")
    overview[1].metric("Residue-region fingerprints", len(report.fingerprints))
    eligible = [item for item in report.candidates if item.eligible]
    overview[2].metric("Eligible residues", len(eligible))
    overview[3].metric("Selected mutations", len(report.mutation_set.selected))

    st.subheader("Dynamic interface fingerprint")
    objectives = {item.region_id: item.objective.value for item in report.config.regions}
    fingerprint_rows = [
        {
            "Residue": item.protein.token,
            "Name": item.protein.resname,
            "Region": item.region_id,
            "Objective": objectives.get(item.region_id, "monitor"),
            "Contact occupancy": item.contact_occupancy,
            "2′-O occupancy": item.o2prime_occupancy,
            "Mean distance during contacts (Å)": item.mean_contact_distance_A,
            "Contact events": item.contact_events,
            "Longest run (frames)": item.longest_run_frames,
            "Nucleotides contacted": item.nucleotide_coverage,
        }
        for item in report.fingerprints
    ]
    st.dataframe(fingerprint_rows, width="stretch", hide_index=True)

    st.subheader("Mutation candidates")
    candidate_rows = [
        {
            "Mutation": item.suggested_mutation,
            "Residue": item.protein.token,
            "Target engagement": item.target_engagement,
            "Preserve burden": item.preservation_burden,
            "Structural risk": item.structural_risk,
            "2′-O signal": item.o2prime_signal,
            "Design score": item.design_score,
            "Target pairs": len(item.target_pairs),
        }
        for item in eligible
    ]
    if candidate_rows:
        st.dataframe(candidate_rows, width="stretch", hide_index=True)
        plot_candidates = eligible[:15]
        figure = go.Figure(
            go.Bar(
                x=[item.design_score for item in plot_candidates],
                y=[item.suggested_mutation for item in plot_candidates],
                orientation="h",
                marker_color=[
                    "#d97706" if item.preservation_burden > 0.25 else "#0b7285"
                    for item in plot_candidates
                ],
                customdata=[item.preservation_burden for item in plot_candidates],
                hovertemplate=(
                    "%{y}<br>design score %{x:.3f}<br>preserve burden "
                    "%{customdata:.1%}<extra></extra>"
                ),
            )
        )
        figure.update_layout(
            template="plotly_white", height=max(320, len(plot_candidates) * 28),
            title="Interpretable residue ranking", xaxis_title="design score",
            yaxis_title="", yaxis_autorange="reversed", margin=dict(l=20, r=20, t=55, b=35),
        )
        st.plotly_chart(figure, width="stretch")
    else:
        st.warning("No eligible candidate meets the current target-occupancy rules.")

    excluded = [item for item in report.candidates if not item.eligible]
    if excluded:
        with st.expander(f"Excluded residues ({len(excluded)})"):
            st.dataframe(
                [
                    {
                        "Residue": item.protein.token,
                        "Name": item.protein.resname,
                        "Reason": item.exclusion_reason,
                    }
                    for item in excluded
                ],
                width="stretch", hide_index=True,
            )

    st.subheader("Complementary mutation set")
    mutation_set = report.mutation_set
    if mutation_set.selected:
        st.success(
            "Suggested evidence set: "
            + ", ".join(item.suggested_mutation for item in mutation_set.selected)
        )
        st.progress(mutation_set.target_pair_coverage)
        st.caption(
            f"Observed target-pair coverage {mutation_set.target_pair_coverage:.1%}; "
            f"preserve burden {mutation_set.preservation_burden:.1%}; "
            f"risk sum {mutation_set.cumulative_risk:.2f}."
        )
    else:
        st.warning("No mutation set satisfies the current constraints.")
    for warning in mutation_set.warnings:
        st.warning(warning)

    if report.truncation_audits:
        st.subheader("Truncation audit")
        for audit in report.truncation_audits:
            with st.container(border=True):
                st.markdown(f"**{audit.truncation.truncation_id}**")
                cols = st.columns(3)
                cols[0].metric("Target removed", f"{audit.target_coverage_removed:.1%}")
                cols[1].metric("Preserve removed", f"{audit.preserve_coverage_removed:.1%}")
                cols[2].metric("Target remaining", f"{audit.unwanted_interaction_remaining:.1%}")
                if audit.distributed_interface_warning:
                    st.warning(audit.interpretation)
                else:
                    st.info(audit.interpretation)
                if audit.flexibility_ratio is not None:
                    st.caption(
                        f"Mean RMSF inside/outside ratio: {audit.flexibility_ratio:.2f}. "
                        "Flexibility alone is not a deletion recommendation."
                    )

    package = build_design_package(report)
    st.download_button(
        "Download design evidence package",
        package,
        file_name=f"{report.source_label.replace(' ', '_')}_engineering.zip",
        mime="application/zip",
        width="stretch",
    )


tab_define, tab_rank, tab_compare = st.tabs(
    ["1 · Define objective", "2 · Rank a trajectory", "3 · Compare a variant"]
)

with tab_define:
    st.subheader("Describe the intervention objective")
    source_label = st.text_input("Condition/run label", "WT replicate 1", key="eng_source")
    protein_selection = st.text_input(
        "Protein selection", "protein", key="eng_protein_selection",
        help="MDAnalysis selection applied to the trajectory topology.",
    )
    topology_upload = st.file_uploader(
        "Optional topology_index.json",
        type=["json"],
        key="eng_topology_index",
        help="Produced by analyze.py; lists the protein and nucleic residue blocks available for selections.",
    )
    if topology_upload is not None:
        try:
            import json
            topology_data = json.loads(topology_upload.read())
            st.dataframe(topology_data.get("blocks", []), width="stretch", hide_index=True)
        except Exception as exc:
            st.error(f"Could not read topology index: {exc}")
    default_regions = [
        {
            "Region ID": "target_region", "Label": "Target interface",
            "Selection": "nucleic and resid 5:16", "Objective": "weaken", "Cutoff Å": 4.0,
        },
        {
            "Region ID": "protected_region", "Label": "Protected interface",
            "Selection": "nucleic and resid 17:30", "Objective": "preserve", "Cutoff Å": 4.0,
        },
    ]
    edited_regions = st.data_editor(
        default_regions,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key="eng_regions",
        column_config={
            "Objective": st.column_config.SelectboxColumn(
                "Objective", options=["weaken", "preserve", "monitor"], required=True
            ),
            "Cutoff Å": st.column_config.NumberColumn(
                "Cutoff Å", min_value=2.0, max_value=8.0, step=0.1, required=True
            ),
        },
    )
    constraint_cols = st.columns(3)
    mutation_budget = constraint_cols[0].number_input(
        "Mutation budget", 1, 30, 5, key="eng_budget"
    )
    min_occupancy = constraint_cols[1].number_input(
        "Minimum occupancy", 0.0, 1.0, 0.05, step=0.01, key="eng_min_occ"
    )
    max_preserve = constraint_cols[2].number_input(
        "Max preserve burden", 0.0, 1.0, 0.40, step=0.05, key="eng_max_preserve"
    )
    protected_text = st.text_input(
        "Protected residues (comma separated)", "",
        placeholder="A:832, A:908",
        key="eng_protected",
    )
    risk_text = st.text_input(
        "Optional residue risks", "",
        placeholder="A:112=0.2, A:362=0.8",
        help="Non-negative user penalties for catalytic, buried, conserved, or otherwise risky residues.",
        key="eng_risks",
    )
    include_truncation = st.checkbox("Audit a proposed truncation", key="eng_do_truncation")
    truncations = ()
    if include_truncation:
        trunc_cols = st.columns(4)
        truncation_id = trunc_cols[0].text_input("Truncation label", "candidate loop")
        truncation_segid = trunc_cols[1].text_input("Protein segid", "A")
        truncation_start = trunc_cols[2].number_input("Start resid", 1, 100000, 230)
        truncation_end = trunc_cols[3].number_input("End resid", 1, 100000, 276)
        truncations = (
            TruncationSpec(
                truncation_id, truncation_segid,
                int(truncation_start), int(truncation_end),
            ),
        )

    try:
        regions = tuple(
            RegionSpec(
                region_id=str(row["Region ID"]).strip(),
                label=str(row["Label"]).strip(),
                selection=str(row["Selection"]).strip(),
                objective=RegionObjective(str(row["Objective"])),
                cutoff_A=float(row["Cutoff Å"]),
            )
            for row in _records(edited_regions)
            if str(row.get("Region ID", "")).strip()
        )
        config = EngineeringConfig(
            protein_selection=protein_selection,
            regions=regions,
            protected_residues=tuple(
                token.strip() for token in protected_text.split(",") if token.strip()
            ),
            mutation_budget=int(mutation_budget),
            min_occupancy=float(min_occupancy),
            max_preservation_burden=float(max_preserve),
            risk_by_residue=_parse_risks(risk_text),
            truncations=truncations,
        )
        st.download_button(
            "Download engineering_config.json",
            config.to_json(),
            file_name="engineering_config.json",
            mime="application/json",
            type="primary",
            width="stretch",
        )
        st.code(
            "python analyze.py --top md_solute.gro --xtc md.xtc -o analysis/ "
            f"--engineering-config engineering_config.json --source-label \"{source_label}\"",
            language="bash",
        )
    except Exception as exc:
        st.error(f"Objective configuration is incomplete: {exc}")

with tab_rank:
    st.subheader("Rank one trajectory")
    use_tutorial = st.toggle(
        "Load fictional interface-design tutorial",
        key="eng_rank_tutorial",
        help="All construct names, residue numbering, and values are invented.",
    )
    uploaded_report = st.file_uploader(
        "Upload engineering.json", type=["json"], key="eng_report_upload"
    )
    report = None
    try:
        if uploaded_report is not None:
            report = load_design_report(uploaded_report.read())
        elif use_tutorial:
            report, _ = load_synthetic_engineering_tutorial()
    except Exception as exc:
        st.error(f"Could not load engineering result: {exc}")
    if report is None:
        st.info(
            "Generate engineering.json with the command from step 1, or load the "
            "synthetic tutorial to inspect the complete design workflow."
        )
    else:
        _render_report(report)

with tab_compare:
    st.subheader("Compare baseline and variant objectives")
    compare_tutorial = st.toggle(
        "Load fictional Reference → Variant A comparison", key="eng_compare_tutorial"
    )
    compare_cols = st.columns(2)
    baseline_upload = compare_cols[0].file_uploader(
        "Baseline engineering.json", type=["json"], key="eng_baseline_upload"
    )
    variant_upload = compare_cols[1].file_uploader(
        "Variant engineering.json", type=["json"], key="eng_variant_upload"
    )
    baseline_report = variant_report = None
    try:
        if baseline_upload is not None and variant_upload is not None:
            baseline_report = load_design_report(baseline_upload.read())
            variant_report = load_design_report(variant_upload.read())
        elif compare_tutorial:
            baseline_report, variant_report = load_synthetic_engineering_tutorial()
    except Exception as exc:
        st.error(f"Could not load comparison: {exc}")

    if baseline_report is None or variant_report is None:
        st.info("Upload both results or load the synthetic comparison.")
    else:
        if baseline_report.provenance.get("data_status") == "fictional_synthetic_tutorial":
            st.info(
                "Fictional tutorial comparison; all construct names, residue numbering, "
                "and values are invented."
            )
        baseline_regions = {
            (region.region_id, region.objective.value)
            for region in baseline_report.config.regions
        }
        variant_regions = {
            (region.region_id, region.objective.value)
            for region in variant_report.config.regions
        }
        if baseline_regions != variant_regions:
            st.error(
                "The two results do not use the same region IDs and objectives. "
                "Recalculate them with one shared engineering_config.json before comparison."
            )
        else:
            comparison = compare_variants(
                baseline_report.config,
                baseline_report.fingerprints,
                variant_report.fingerprints,
                baseline_report.source_label,
                variant_report.source_label,
            )
            rows = [
                {
                    "Region": item.region_id,
                    "Objective": item.objective.value,
                    "Baseline mass": item.baseline_mass,
                    "Variant mass": item.variant_mass,
                    "Retention": (
                        None if item.retention_pct is None else item.retention_pct / 100
                    ),
                    "Objective result": item.objective_change,
                }
                for item in comparison.regions
            ]
            st.dataframe(rows, width="stretch", hide_index=True)
            st.caption(
                "Region mass is the sum of residue–nucleotide contact occupancies. "
                "Single-run changes are descriptive, not inferential."
            )
            package = build_design_package(variant_report, comparison=comparison)
            st.download_button(
                "Download variant-comparison evidence package",
                package,
                file_name="guided_variant_comparison.zip",
                mime="application/zip",
                width="stretch",
            )

st.markdown("[Open the fictional Variant A tutorial →](/variant-a)")
render_footer()
