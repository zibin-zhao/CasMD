"""StrandMD entrypoint — task-oriented navigation and homepage.

Welcome / Workflow / Handbook / About sections. Page set_page_config is
owned here (per Streamlit's st.navigation contract).
"""
from __future__ import annotations
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from app.shared import state
from app.shared.styles import inject_css
from app.shared.footer import render_footer

# ---------- ONE set_page_config for the whole app ----------
st.set_page_config(
    page_title="StrandMD — protein–nucleic acid dynamics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="auto",
)


def home_page() -> None:
    """Task-oriented landing for preparation, analysis, and examples."""
    inject_css()

    # Top nav: logo (left) + section links (right)
    nav_cols = st.columns([2, 3])
    with nav_cols[0]:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;padding-top:8px">'
            '<div style="width:36px;height:36px;border-radius:10px;background:#0b7285;'
            'color:white;display:flex;align-items:center;justify-content:center;font-size:19px">≋</div>'
            '<span style="font-weight:700;font-size:20px;letter-spacing:-0.02em">StrandMD</span>'
            '</div>', unsafe_allow_html=True,
        )
    with nav_cols[1]:
        st.markdown(
            '<div style="display:flex;gap:20px;justify-content:center;padding-top:18px;font-size:14px">'
            '<a href="/engineer" target="_self" '
            'style="color:#1d1d1f;text-decoration:none;opacity:0.75">Engineer</a>'
            '<a href="/prepare" target="_self" '
            'style="color:#1d1d1f;text-decoration:none;opacity:0.75">Prepare</a>'
            '<a href="/analyze" target="_self" '
            'style="color:#1d1d1f;text-decoration:none;opacity:0.75">Analyze</a>'
            '<a href="/overview" target="_self" '
            'style="color:#1d1d1f;text-decoration:none;opacity:0.75">Handbook</a>'
            '<a href="/acknowledgements" target="_self" '
            'style="color:#1d1d1f;text-decoration:none;opacity:0.75">Acknowledgements</a>'
            '<a href="https://github.com/zibin-zhao/CasMD" target="_blank" '
            'style="color:#1d1d1f;text-decoration:none;opacity:0.75">GitHub ↗</a>'
            '</div>', unsafe_allow_html=True,
        )

    # Hero
    st.markdown(
        '<div style="text-align:center;padding:62px 0 26px">'
        '<div style="font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;'
        'color:#0b7285;margin-bottom:14px">Protein · DNA · RNA</div>'
        '<h1 style="font-size:52px;letter-spacing:-0.04em;margin:0 0 18px;line-height:1.06">'
        'From trajectory to <span style="color:#0b7285">testable protein design</span>.</h1>'
        '<p style="font-size:16px;color:#6e6e73;max-width:640px;margin:0 auto 28px;line-height:1.5">'
        'Define an interface objective, diagnose dynamic contacts, design mutations '
        'or truncations, run on your own compute, and compare the resulting variants.</p>'
        '</div>', unsafe_allow_html=True,
    )

    cta_cols = st.columns([0.6, 1.3, 1.3, 1.3, 0.6])
    with cta_cols[1]:
        if st.button("Engineer a variant →", type="primary",
                     width="stretch", key="cta_engineer"):
            st.switch_page("pages/3_Engineer.py")
    with cta_cols[2]:
        if st.button("Prepare a simulation →", type="secondary",
                     width="stretch", key="cta_prepare"):
            st.session_state["workflow_target"] = "prepare"
            state.request_workflow_start(st.session_state)
            if state.is_privacy_acked(st.session_state):
                st.switch_page("pages/1_Stage_1_Predict_and_Bundle.py")
    with cta_cols[3]:
        if st.button("Analyze results →", type="secondary",
                     width="stretch", key="cta_analyze"):
            st.session_state["workflow_target"] = "analyze"
            state.request_workflow_start(st.session_state)
            if state.is_privacy_acked(st.session_state):
                st.switch_page("pages/2_Stage_2_Results_and_Viz.py")

    demo_cols = st.columns([1.5, 1, 1.5])
    with demo_cols[1]:
        if st.button(
            "Explore fictional Variant A",
            type="secondary",
            width="stretch",
            key="cta_example",
        ):
            st.switch_page("pages/examples/Variant_A.py")

    # Privacy modal (only if user clicked Start workflow but hasn't acked)
    if state.show_privacy_modal_now(st.session_state):
        with st.container(border=True):
            st.subheader("⚠️ Privacy disclaimer")
            st.markdown(
                "**Do not upload unpublished or proprietary sequences.** "
                "If you run StrandMD on Hugging Face Spaces, sequences and intermediate "
                "files transit a public cloud environment and may be visible to "
                "platform operators. For sensitive work, run StrandMD locally "
                "(`docker run -p 8501:8501 casmd`) instead."
            )
            acked = st.checkbox(
                "I understand and accept these terms.",
                value=state.is_privacy_acked(st.session_state),
                key="modal_ack",
            )
            if acked:
                state.set_privacy_acked(st.session_state, True)
                target = st.session_state.get("workflow_target", "prepare")
                if target == "analyze":
                    st.switch_page("pages/2_Stage_2_Results_and_Viz.py")
                st.switch_page("pages/1_Stage_1_Predict_and_Bundle.py")

    # Trust line
    st.markdown(
        '<div style="text-align:center;margin-top:50px">'
        '<div style="font-size:12px;color:#6e6e73;margin-bottom:16px">Powered by</div>'
        '<div style="display:flex;gap:36px;justify-content:center;flex-wrap:wrap;color:#86868b;font-weight:600;font-size:14px">'
        '<span style="opacity:0.65">AlphaFold 3</span>'
        '<span style="opacity:0.65">Boltz-2</span>'
        '<span style="opacity:0.65">Protenix</span>'
        '<span style="opacity:0.65">AmberTools</span>'
        '<span style="opacity:0.65">GROMACS</span>'
        '<span style="opacity:0.65">MDAnalysis</span>'
        '</div></div>', unsafe_allow_html=True,
    )

    # Product loop
    st.markdown('<div style="margin-top:48px"></div>', unsafe_allow_html=True)
    st.markdown(
        '<h2 style="text-align:center;margin-bottom:22px">Turn dynamics into an engineering decision</h2>',
        unsafe_allow_html=True,
    )
    card_cols = st.columns(3)
    cards_content = [
        ("01", "Diagnose the interface", "Measure region-specific occupancy, lifetimes, distances, and RNA 2′-O contacts."),
        ("02", "Design interventions", "Rank interpretable mutations and audit whether a proposed truncation covers the interface."),
        ("03", "Compare variants", "Track weaken and preserve objectives across conditions and independent replicates."),
    ]
    for col, (icon, title, desc) in zip(card_cols, cards_content):
        with col:
            st.markdown(
                f'<div class="casmd-card" style="margin-bottom:14px;min-height:128px">'
                f'<div style="display:flex;align-items:flex-start;gap:12px">'
                f'<div style="width:44px;height:44px;border-radius:12px;'
                f'background:rgba(48,176,199,0.15);color:#30b0c7;font-size:22px;'
                f'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
                f'font-size:13px;font-weight:700">{icon}</div>'
                f'<div>'
                f'<div style="font-size:14px;font-weight:600;color:#1d1d1f;margin-bottom:3px">{title}</div>'
                f'<div style="font-size:12px;color:#6e6e73;line-height:1.45">{desc}</div>'
                f'</div></div></div>', unsafe_allow_html=True,
            )

    render_footer()


# ---------- Global CSS (rendered before nav) ----------
inject_css()


# ---------- Page registry ----------
pg = st.navigation(
    {
        "Welcome": [
            st.Page(home_page, title="Home", icon="🏠", url_path="home", default=True),
            st.Page("pages/Setup.py", title="Setup", icon="⚙️", url_path="setup"),
        ],
        "Workflow": [
            st.Page("pages/3_Engineer.py",
                    title="Engineer", url_path="engineer"),
            st.Page("pages/1_Stage_1_Predict_and_Bundle.py",
                    title="Prepare", url_path="prepare"),
            st.Page("pages/2_Stage_2_Results_and_Viz.py",
                    title="Analyze & Compare", url_path="analyze"),
        ],
        "Examples": [
            st.Page("pages/examples/Variant_A.py",
                    title="Variant A tutorial", url_path="variant-a"),
        ],
        "Handbook": [
            st.Page("pages/handbook/01_Overview.py",
                    title="Overview", url_path="overview"),
            st.Page("pages/handbook/02_Background.py",
                    title="Background", url_path="background"),
            st.Page("pages/handbook/03_Walkthrough.py",
                    title="Walkthrough", url_path="walkthrough"),
            st.Page("pages/handbook/04_Reference.py",
                    title="Reference", url_path="reference"),
        ],
        "About": [
            st.Page("pages/about/Acknowledgements.py",
                    title="Acknowledgements", url_path="acknowledgements"),
        ],
    }
)

pg.run()
