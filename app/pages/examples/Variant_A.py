"""Fictional Variant A interface-engineering tutorial."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import plotly.graph_objects as go
import streamlit as st

from app.shared.demo_run import render_demo_run
from app.shared.examples import (
    CONTROL_RETENTION,
    VARIANT_CONSTRUCTS,
    VARIANT_METRICS,
    VARIANT_PROJECT,
    VARIANT_RETENTION,
)
from app.shared.footer import render_footer
from app.shared.styles import inject_css


inject_css()

st.caption("FICTIONAL TUTORIAL · SYNTHETIC VALUES")
st.title("Variant A: a trajectory-guided interface design")
st.markdown(
    "This worked example shows how StrandMD can turn region-specific dynamics "
    "into a mutation hypothesis while preserving a second functional interface."
)
st.warning(
    "Everything on this page is fictional: construct names, residue numbering, "
    "measurements, and outcomes. It is not derived from an unpublished case study "
    "and must not be interpreted as biological evidence."
)

overview = st.columns(3)
overview[0].metric("Conditions represented", len(VARIANT_PROJECT.conditions))
overview[1].metric("Synthetic runs", VARIANT_PROJECT.replicate_count)
overview[2].metric("Independent runs / condition", "1")
st.caption(
    "The synthetic single-run values demonstrate the interface only. A real study "
    "requires independently initialized replicates and experimental validation."
)

st.header("Design question")
st.info(VARIANT_PROJECT.hypothesis)

st.header("Fictional construct logic")
st.dataframe(VARIANT_CONSTRUCTS, width="stretch", hide_index=True)

st.header("Illustrative trajectory summary")
st.dataframe(VARIANT_METRICS, width="stretch", hide_index=True)

metric_names = list(VARIANT_RETENTION)
metric_values = list(VARIANT_RETENTION.values())
retention_fig = go.Figure(
    go.Bar(
        x=metric_values,
        y=metric_names,
        orientation="h",
        marker_color=["#d97706", "#0b7285", "#0b7285"],
        text=[f"{value}%" for value in metric_values],
        textposition="outside",
    )
)
retention_fig.add_vline(x=100, line_dash="dash", line_color="#60717b")
retention_fig.update_layout(
    template="plotly_white",
    title="Fictional Variant A retention relative to its reference",
    xaxis_title="retained synthetic signal (%)",
    yaxis_title="",
    xaxis_range=[0, 115],
    height=320,
    margin=dict(l=20, r=35, t=55, b=35),
    showlegend=False,
)
st.plotly_chart(retention_fig, width="stretch")

st.header("Why controls matter")
control_fig = go.Figure(
    go.Bar(
        x=list(CONTROL_RETENTION),
        y=list(CONTROL_RETENTION.values()),
        marker_color=["#60717b", "#60717b", "#60717b", "#d97706"],
        text=[f"{value}%" for value in CONTROL_RETENTION.values()],
        textposition="outside",
    )
)
control_fig.add_hline(y=100, line_dash="dash", line_color="#60717b")
control_fig.update_layout(
    template="plotly_white",
    title="Synthetic target-region contact retention",
    yaxis_title="retained synthetic contacts (%)",
    yaxis_range=[0, 115],
    height=320,
    margin=dict(l=20, r=20, t=55, b=35),
    showlegend=False,
)
st.plotly_chart(control_fig, width="stretch")
st.markdown(
    "In this invented scenario, the control edits do not sufficiently weaken the "
    "target region, so the workflow ranks complementary interface substitutions."
)

st.header("Decision rule")
st.markdown(
    "A candidate advances only if it reduces the intended interaction while "
    "preserving global protein quality and the protected interface. A global loss "
    "of activity is failure, not selectivity."
)

with st.expander("Evidence limits for any real project", expanded=True):
    st.markdown(
        "- use independently initialized simulation replicates\n"
        "- report between-replicate uncertainty\n"
        "- verify equivalent residue mapping across variants\n"
        "- measure expression, folding, binding, and activity experimentally\n"
        "- publish real case details only after the manuscript or preprint is ready"
    )

st.download_button(
    "Download fictional project manifest",
    json.dumps(VARIANT_PROJECT.to_manifest(), indent=2),
    file_name="fictional_variant_a_project.json",
    mime="application/json",
    width="stretch",
)

st.header("Try the interface")
st.caption("The interactive dashboard uses a separate synthetic trajectory.")
render_demo_run(label="Open synthetic dashboard demo", key="variant_a_demo")

render_footer()
