"""StrandMD scientific-workbench theme."""
from __future__ import annotations

import streamlit as st


CSS = """
<style>
/* ---------- Typography ---------- */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=block');

html, body {
    font-family: -apple-system, "SF Pro Display", "SF Pro Text", BlinkMacSystemFont,
                  "Outfit", system-ui, sans-serif !important;
    color: #1d1d1f !important;
    -webkit-font-smoothing: antialiased;
}

h1, h2, h3, h4, h5, h6 {
    font-family: inherit !important;
    color: #1d1d1f !important;
    letter-spacing: -0.025em;
    font-weight: 600;
}
h1 { font-size: 2.6rem; letter-spacing: -0.04em; }
h2 { font-size: 1.55rem; }
h3 { font-size: 1.2rem; }

p, span, label, div, .stMarkdown { color: #1d1d1f; }
.subtitle, .stCaption, [data-testid="stCaptionContainer"] { color: #6e6e73 !important; }

/* ---------- Page background ---------- */
.stApp {
    background:
        linear-gradient(180deg, rgba(11,114,133,0.06) 0, transparent 220px),
        #f6f8fa !important;
    color: #1d1d1f !important;
    min-height: 100vh;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #dfe4e8;
}
section[data-testid="stSidebar"] * { color: #1d1d1f; }
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    border-radius: 10px;
    padding: 8px 12px;
    margin-bottom: 2px;
    font-size: 13px;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: #0b7285 !important;
    color: white !important;
}

/* ---------- Card entrance animation ---------- */
@keyframes card-enter {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ---------- Scientific card ---------- */
.casmd-card,
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid #dfe4e8 !important;
    border-radius: 12px !important;
    padding: 22px 26px !important;
    box-shadow: 0 4px 14px rgba(22,34,51,0.05) !important;
    margin-bottom: 16px;
    animation: card-enter 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Accent card */
.casmd-card-accent {
    background: linear-gradient(135deg, #0b7285 0%, #075867 100%);
    color: white;
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 18px;
    padding: 22px 26px;
    box-shadow:
        0 10px 30px rgba(11,114,133,0.24),
        inset 0 1px 0 rgba(255,255,255,0.25);
    margin-bottom: 16px;
}
.casmd-card-accent, .casmd-card-accent * { color: white !important; }

/* ---------- KPI ---------- */
.casmd-kpi-value {
    font-size: clamp(1.65rem, 2.2vw, 2.4rem);
    font-weight: 600;
    letter-spacing: -0.035em;
    line-height: 1.0;
    white-space: nowrap;
}
.casmd-kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em;
                   opacity: 0.6; margin-top: 6px; font-weight: 500; }

/* ---------- Step indicator chips ---------- */
.casmd-stepper { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin: 16px 0 28px; }
.casmd-chip {
    padding: 6px 14px; border-radius: 999px;
    font-size: 0.78rem; font-weight: 500;
    background: rgba(255,255,255,0.6);
    color: #6e6e73;
    border: 1px solid rgba(0,0,0,0.05);
    backdrop-filter: blur(20px);
}
.casmd-chip.active {
    background: #0b7285;
    color: white;
    border-color: rgba(255,255,255,0.4);
    box-shadow: 0 4px 14px rgba(11,114,133,0.28);
}
.casmd-chip.done { background: rgba(11,114,133,0.10); color: #0b7285; border-color: rgba(11,114,133,0.2); }
.casmd-chip .chip-num {
    display: inline-block; width: 18px; height: 18px;
    line-height: 18px; text-align: center;
    font-weight: 600; margin-right: 6px; opacity: 0.85;
}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {
    font-family: inherit !important;
    font-weight: 500 !important;
    border-radius: 999px !important;
    padding: 0.6rem 1.4rem !important;
    transition: transform 0.12s, box-shadow 0.2s !important;
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0b7285 0%, #075867 100%) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.4) !important;
    box-shadow: 0 8px 22px rgba(11,114,133,0.22), inset 0 1px 0 rgba(255,255,255,0.25) !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover { transform: translateY(-1px); }
.stButton > button[kind="primary"]:disabled {
    background: rgba(200,200,210,0.4) !important;
    color: rgba(0,0,0,0.4) !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}
.stButton > button[kind="secondary"] {
    background: #ffffff !important;
    color: #1d1d1f !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    backdrop-filter: blur(20px) !important;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    background: #eef2f4;
    border: 1px solid rgba(0,0,0,0.05);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] { color: #6e6e73; border-radius: 8px; padding: 0.5rem 1.1rem; }
.stTabs [aria-selected="true"] {
    background: #0b7285 !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(11,114,133,0.22);
}

/* ---------- Inputs ---------- */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
.stTextInput > div > div, .stNumberInput > div > div, .stTextArea > div > div {
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    border-radius: 12px !important;
}
input, textarea {
    background: transparent !important;
    color: #1d1d1f !important;
    -webkit-text-fill-color: #1d1d1f !important;
}
input::placeholder, textarea::placeholder { color: #86868b !important; -webkit-text-fill-color: #86868b !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
    border-color: #0b7285 !important;
    box-shadow: 0 0 0 3px rgba(11,114,133,0.12) !important;
}

/* ---------- Progress ---------- */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #0b7285, #075867) !important;
}

/* ---------- Brand wordmark (top-left fixed) ---------- */
.casmd-brand {
    position: fixed; top: 18px; left: 22px;
    font-weight: 700; font-size: 1.1rem; letter-spacing: -0.01em;
    color: #1d1d1f; z-index: 1000; pointer-events: none;
}
.casmd-brand .dot { color: #0b7285; }

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] {
    background: #ffffff;
    border-radius: 14px;
    border: 1px dashed rgba(0,0,0,0.12);
    padding: 6px;
}

/* ---------- Material Symbols preservation ---------- */
.material-icons, .material-symbols-outlined, [class*="material-icons"], [class*="material-symbols"],
[data-testid="stIconMaterial"], [data-testid="stIconMaterial"] * {
    font-family: 'Material Symbols Outlined', 'Material Icons' !important;
    font-feature-settings: 'liga' !important;
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def card(html_body: str, accent: bool = False) -> None:
    cls = "casmd-card-accent" if accent else "casmd-card"
    st.markdown(f'<div class="{cls}">{html_body}</div>', unsafe_allow_html=True)


def kpi(value: str, label: str) -> str:
    return (f'<div class="casmd-kpi-value">{value}</div>'
            f'<div class="casmd-kpi-label">{label}</div>')
