"""Handbook · 05_Force_fields."""
import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.shared.handbook import render_handbook_page
render_handbook_page("05_force_fields.md")
