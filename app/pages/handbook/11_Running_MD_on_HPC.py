"""Handbook · 11_Running_MD_on_HPC."""
import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.shared.handbook import render_handbook_page
render_handbook_page("11_running_md_on_hpc.md")
