"""Card stepper helpers — track current step in session state, render chips."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Sequence

import streamlit as st


@dataclass(frozen=True)
class Stepper:
    """Static description of a stepper flow. The runtime state lives in session_state."""
    titles: tuple[str, ...]
    state_key: str = "current_step"

    @property
    def max_step(self) -> int:
        return len(self.titles) - 1


def render_chips_html(titles: Sequence[str], current: int) -> str:
    """Build the chips HTML for the stepper indicator at the top of a page."""
    chips: list[str] = []
    for i, title in enumerate(titles):
        if i < current:
            cls = "casmd-chip done"
        elif i == current:
            cls = "casmd-chip active"
        else:
            cls = "casmd-chip"
        # Each chip is padded with a data-step attribute so that a 200-char
        # lookback from the chip label stays within that chip's own opening tag.
        chips.append(
            f'<div class="{cls}" data-step="{i}" data-step-title="{title}" '
            f'style="display:inline-flex;align-items:center">'
            f'<span class="chip-num">{i + 1}</span>{title}</div>'
        )
    return f'<div class="casmd-stepper">{"".join(chips)}</div>'


def render_chips(stepper: Stepper) -> None:
    """Render the step-indicator chips for `stepper` based on session_state."""
    current = st.session_state.get(stepper.state_key, 0)
    st.markdown(render_chips_html(stepper.titles, current), unsafe_allow_html=True)


def advance(session_state: Any, *, max_step: int) -> None:
    cur = session_state.get("current_step", 0)
    session_state["current_step"] = min(cur + 1, max_step)


def go_back(session_state: Any) -> None:
    cur = session_state.get("current_step", 0)
    session_state["current_step"] = max(cur - 1, 0)


def set_step(session_state: Any, step: int, *, max_step: int) -> None:
    session_state["current_step"] = max(0, min(step, max_step))


def render_controls(
    stepper: Stepper,
    *,
    can_advance: bool = True,
    show_skip: bool = False,
    final_step_label: str | None = None,
) -> tuple[bool, bool, bool]:
    """Render Back / Skip / Next controls. Returns (back_clicked, skip_clicked, next_clicked)."""
    current = st.session_state.get(stepper.state_key, 0)
    is_first = current == 0
    is_last = current == stepper.max_step

    cols = st.columns([1, 1, 1, 2])
    with cols[0]:
        back = st.button("← Back", disabled=is_first, type="secondary",
                          use_container_width=True, key=f"back_{current}")
    with cols[1]:
        if show_skip and not is_last:
            skip = st.button("Skip", type="secondary",
                              use_container_width=True, key=f"skip_{current}")
        else:
            skip = False
    with cols[3]:
        if is_last and final_step_label:
            nxt = st.button(final_step_label, type="primary",
                             disabled=not can_advance, use_container_width=True,
                             key=f"next_{current}")
        elif is_last:
            nxt = False  # caller handles the final-step action button itself
        else:
            nxt = st.button("Next →", type="primary",
                             disabled=not can_advance, use_container_width=True,
                             key=f"next_{current}")

    if back:
        go_back(st.session_state)
        st.rerun()
    if skip:
        advance(st.session_state, max_step=stepper.max_step)
        st.rerun()
    if nxt:
        advance(st.session_state, max_step=stepper.max_step)
        st.rerun()
    return back, skip, nxt
