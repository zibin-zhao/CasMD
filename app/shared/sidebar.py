"""Sidebar adornments: CasMD logo (top) + Hsing Group logo (bottom)."""
from __future__ import annotations
from pathlib import Path

import streamlit as st


_ASSETS = Path(__file__).resolve().parent.parent / "assets"


def render_sidebar_brand() -> None:
    """Top of sidebar: CasMD logo + wordmark."""
    logo = _ASSETS / "logo-casmd.png"
    if logo.exists():
        st.sidebar.image(str(logo), width=180)
    else:
        st.sidebar.markdown("### Cas·MD")
    st.sidebar.markdown(
        '<p style="opacity:0.6;font-size:0.8rem;margin-top:-8px">'
        'Protein–nucleic acid MD</p>',
        unsafe_allow_html=True,
    )


def render_sidebar_lab_logo() -> None:
    """Bottom of sidebar: Hsing Group logo + 'Made at...' line."""
    logo = _ASSETS / "logo-hsing-group.png"
    st.sidebar.markdown(
        '<div style="height:1px;background:rgba(0,0,0,0.08);margin:18px 0"></div>',
        unsafe_allow_html=True,
    )
    cols = st.sidebar.columns([1, 3])
    with cols[0]:
        if logo.exists():
            st.image(str(logo), width=40)
    with cols[1]:
        st.markdown(
            '<p style="font-size:0.75rem;color:#6e6e73;line-height:1.3;margin:0">'
            'Made at <strong>Hsing Lab</strong>, HKUST</p>',
            unsafe_allow_html=True,
        )
