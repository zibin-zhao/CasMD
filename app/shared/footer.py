"""Consistent footer rendered on every StrandMD page."""
from __future__ import annotations
import streamlit as st
from casmd import __version__


_FOOTER_HTML = f"""
<div style="margin-top:60px; padding:18px 0; text-align:center;
            color:#6e6e73; font-size:11px; border-top:1px solid rgba(0,0,0,0.06)">
    <span>StrandMD <strong>v{__version__}</strong></span>
    &nbsp;·&nbsp;
    <span>Made at <strong>Hsing Lab</strong>, HKUST</span>
    &nbsp;·&nbsp;
    <a href="https://github.com/zibin-zhao/CasMD" target="_blank"
       style="color:#6e6e73;text-decoration:none">⭐ GitHub</a>
    &nbsp;·&nbsp;
    <a href="/acknowledgements" target="_self"
       style="color:#6e6e73;text-decoration:none">📝 Cite</a>
    &nbsp;·&nbsp;
    <span>MIT license</span>
</div>
"""


def render_footer() -> None:
    """Render the standard StrandMD footer at the bottom of the current page."""
    st.markdown(_FOOTER_HTML, unsafe_allow_html=True)
