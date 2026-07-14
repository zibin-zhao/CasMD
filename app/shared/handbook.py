"""Helper for rendering handbook pages from markdown content files."""
from __future__ import annotations
from pathlib import Path

import streamlit as st

from app.shared.styles import inject_css


_CONTENT_DIR = Path(__file__).resolve().parent.parent / "handbook_content"


def render_handbook_page(content_filename: str, hero_image: str | None = None) -> None:
    """Render a single handbook page from `app/handbook_content/<content_filename>`.

    With st.navigation(), st.set_page_config() is owned by the entrypoint —
    individual pages must NOT call it. We still inject CSS so each page is
    self-contained when opened via AppTest.

    Args:
        content_filename: Markdown file under app/handbook_content/ to load.
        hero_image: Optional filename under app/assets/ to render as a hero
            image at the top of the page (above the markdown body).
    """
    inject_css()

    path = _CONTENT_DIR / content_filename
    if not path.exists():
        st.error(f"Handbook content missing: {content_filename}")
        return
    md = path.read_text()
    with st.container(border=True):
        if hero_image:
            assets_dir = Path(__file__).resolve().parent.parent / "assets"
            hero_path = assets_dir / hero_image
            if hero_path.exists():
                st.image(str(hero_path), use_container_width=True)
        st.markdown(md, unsafe_allow_html=True)
    from app.shared.footer import render_footer
    render_footer()
