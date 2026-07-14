"""Parse GROMACS mdrun log lines into structured progress events.

mdrun emits step lines like:
    step 12345000, t = 24690.000 ps, kT = 308.4
and at the end:
    Performance:       47.823       0.502
"""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressEvent:
    """One snapshot of mdrun progress."""
    current_step: int | None = None
    current_time_ps: float | None = None
    total_steps: int | None = None
    total_time_ps: float | None = None
    ns_per_day: float | None = None


# Matches: "step 12345000, t = 24690.000 ps"  (case-insensitive)
_STEP_RE = re.compile(
    r"step\s+(\d+)\s*,\s*t\s*=\s*([\d.]+)\s*ps",
    re.IGNORECASE,
)

# Matches the end-of-run performance summary
_PERF_RE = re.compile(
    r"Performance:\s+([\d.]+)\s+([\d.]+)",
)


def parse_progress_line(line: str) -> ProgressEvent | None:
    """Return a ProgressEvent if the line carries any known metric, else None."""
    if not line or line.lstrip().startswith("#"):
        return None

    perf = _PERF_RE.search(line)
    if perf:
        return ProgressEvent(ns_per_day=float(perf.group(1)))

    step = _STEP_RE.search(line)
    if step:
        return ProgressEvent(
            current_step=int(step.group(1)),
            current_time_ps=float(step.group(2)),
        )

    return None


def percent_complete(current_step: int, total_steps: int) -> float:
    """Return percent in [0, 100]. 0 when total_steps is unknown."""
    if total_steps <= 0:
        return 0.0
    return min(100.0, 100.0 * current_step / total_steps)
