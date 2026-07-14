"""Session-state keys + tiny helpers used by every Streamlit page."""
from __future__ import annotations
import datetime
from typing import Any

# Session-state keys (centralized so a typo doesn't silently break a page)
PRIVACY_ACKED = "privacy_acked"
JOB_NAME = "job_name"
SELECTED_PDB = "selected_pdb"
PRED_BUNDLES = "pred_bundles"
BUILD_CONFIG = "build_config"
BUNDLE_SPEC = "bundle_spec"


def default_job_name() -> str:
    """A safe default job-name like 'strandmd_20260711_103412'."""
    return "strandmd_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def is_privacy_acked(session_state: Any) -> bool:
    return bool(session_state.get(PRIVACY_ACKED, False))


def set_privacy_acked(session_state: Any, value: bool) -> None:
    session_state[PRIVACY_ACKED] = value


# Plan 5.5 additions
BUILD_DONE = "build_done"           # bool — set True after a successful build
BUILD_OUTPUT_ZIP = "build_zip"      # str path — the produced bundle zip
BUILD_ELAPSED_S = "build_elapsed_s" # float — wall time of the last build


def reset_build(session_state) -> None:
    """Clear all build-related session keys (called by the 'Reset' button)."""
    for k in (
        BUILD_DONE, BUILD_OUTPUT_ZIP, BUILD_ELAPSED_S, SELECTED_PDB,
        BUILD_CONFIG, BUNDLE_SPEC,
    ):
        session_state.pop(k, None)


# Plan-redesign additions
PRIVACY_MODAL_SHOWN = "privacy_modal_shown"   # has the modal been displayed this session
WORKFLOW_STARTED = "workflow_started"         # set True after user clicks Start workflow


def workflow_can_start(session_state) -> bool:
    """Returns True if user has acked privacy disclaimer."""
    return is_privacy_acked(session_state)


def request_workflow_start(session_state) -> None:
    """Called when user clicks 'Start workflow'. Triggers modal if not yet acked."""
    session_state[PRIVACY_MODAL_SHOWN] = True
    session_state[WORKFLOW_STARTED] = True


def show_privacy_modal_now(session_state) -> bool:
    """True if the modal should render on this rerun."""
    return session_state.get(PRIVACY_MODAL_SHOWN, False) and not is_privacy_acked(session_state)
