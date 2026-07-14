"""The example-analysis CTA — an environment-aware demonstration run.

Behaviour depends on where StrandMD is deployed:

* **Hosted HF Space** (2 vCPU, no GPU — CASMD_LOCAL_RUN_ENABLED unset):
  a compute-free *replay*. We emit synthetic ProgressEvents in the exact shape
  mdrun produces, animate them, then route to Stage 2 where the bundled example
  analysis dashboard renders. No GROMACS is invoked, so it is
  fast and safe under concurrent public load.

* **Local / Docker** (CASMD_LOCAL_RUN_ENABLED=1): the replay still plays, and a
  caption points users to Stage 1's existing 'Run MD now' panel
  (app.shared.local_run) for a real GPU simulation.
"""
from __future__ import annotations

import time

from casmd.run.progress import ProgressEvent, percent_complete

DEFAULT_TOTAL_PS = 10.0
DEFAULT_N_UPDATES = 24
DEFAULT_NS_PER_DAY = 3.0
DEFAULT_DELAY_S = 0.13
_TIMESTEP_FS = 2.0


def replay_progress_events(
    total_ps: float = DEFAULT_TOTAL_PS,
    n_updates: int = DEFAULT_N_UPDATES,
    ns_per_day: float = DEFAULT_NS_PER_DAY,
    timestep_fs: float = _TIMESTEP_FS,
) -> list[ProgressEvent]:
    """Synthetic mdrun-shaped progress for the compute-free demo replay.

    Returns `n_updates` events whose simulated time ramps linearly from >0 to
    `total_ps`. Only the final event carries `ns_per_day` — mdrun prints the
    performance line once, at the end. No GROMACS is involved.
    """
    total_steps = int(round(total_ps * 1000.0 / timestep_fs))
    events: list[ProgressEvent] = []
    for i in range(1, n_updates + 1):
        last = i == n_updates
        frac = i / n_updates
        step = total_steps if last else int(round(total_steps * frac))
        t = total_ps if last else total_ps * frac
        events.append(
            ProgressEvent(
                current_step=step,
                current_time_ps=t,
                total_steps=total_steps,
                total_time_ps=total_ps,
                ns_per_day=ns_per_day if last else None,
            )
        )
    return events


def render_demo_run(
    *,
    primary: bool = False,
    delay_s: float = DEFAULT_DELAY_S,
    key: str = "cta_run_demo",
    label: str = "Explore synthetic analysis demo",
) -> None:
    """Render the example CTA and, on click, play the replay + navigate.

    primary: render as a filled primary button (the hero's main call-to-action).
    """
    import streamlit as st

    from app.shared import state
    from app.shared.local_run import is_local_run_enabled

    clicked = st.button(
        label,
        type="primary" if primary else "secondary",
        width="stretch",
        key=key,
        help="Explore pre-computed trajectory metrics in the interactive dashboard "
             "without signup or upload.",
    )
    if is_local_run_enabled():
        st.caption(
            "On a local GPU build? Head to **Stage 1** to build your own system "
            "and run a **real** MD simulation."
        )
    if not clicked:
        return

    # Demo data is public — bypass the privacy ack before routing to Stage 2.
    state.set_privacy_acked(st.session_state, True)
    st.session_state["use_demo_data"] = True

    events = replay_progress_events()
    with st.status("Loading pre-computed example…", expanded=True) as status:
        bar = st.progress(0.0)
        line = st.empty()
        for evt in events:
            bar.progress(percent_complete(evt.current_step, evt.total_steps) / 100.0)
            msg = f"step {evt.current_step:,}, t = {evt.current_time_ps:.1f} ps"
            if evt.ns_per_day:
                msg += f"  ·  {evt.ns_per_day:.1f} ns/day (example replay)"
            line.write(msg)
            time.sleep(delay_s)
        status.update(
            label="✓ Example ready — opening the analysis…",
            state="complete",
            expanded=False,
        )

    st.switch_page("pages/2_Stage_2_Results_and_Viz.py")
