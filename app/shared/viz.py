"""Pure helpers for the visualization dashboard.

`parse_dat_file` reads a 2-column whitespace-delimited `.dat` (comments
skipped). Plot helpers use StrandMD's light scientific-workbench theme.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import plotly.graph_objects as go


def parse_dat_file(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Parse a two-column whitespace-delimited .dat file, skipping `#` lines."""
    xs: list[float] = []
    ys: list[float] = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            xs.append(float(parts[0]))
            ys.append(float(parts[1]))
        except ValueError:
            continue
    return np.array(xs), np.array(ys)


def plot_xy(x: np.ndarray, y: np.ndarray, *, title: str,
             x_label: str, y_label: str, line_color: str = "#0b7285") -> go.Figure:
    """Build a light scientific Plotly line chart."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color=line_color, width=1.5),
        hovertemplate=f"{x_label}: %{{x:.3f}}<br>{y_label}: %{{y:.3f}}<extra></extra>",
    ))
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#1d1d1f", size=12),
        margin=dict(l=40, r=20, t=40, b=40),
        height=320,
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.08)", zerolinecolor="rgba(0,0,0,0.12)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)", zerolinecolor="rgba(0,0,0,0.12)")
    return fig


def plot_overlay(*, x, y_a, y_b, label_a: str, label_b: str,
                 title: str, x_label: str, y_label: str):
    """Two-line overlay plot for trajectory comparison."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y_a, name=label_a, mode="lines",
        line=dict(color="#30b0c7", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=x, y=y_b, name=label_b, mode="lines",
        line=dict(color="#ff6b6b", width=2),
    ))
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, SF Pro Display, system-ui, sans-serif",
                  color="#1d1d1f"),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.08)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)")
    return fig


def plot_delta(*, x, delta, title: str, x_label: str, y_label: str):
    """Difference (B - A) plot rendered below an overlay."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=delta, name="Δ", mode="lines",
        line=dict(color="#86868b", width=1.5),
        fill="tozeroy", fillcolor="rgba(48,176,199,0.15)",
    ))
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, SF Pro Display, system-ui, sans-serif",
                  color="#1d1d1f"),
        showlegend=False,
        height=160,
        margin=dict(l=40, r=20, t=40, b=30),
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.08)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)", zeroline=True,
                     zerolinecolor="rgba(0,0,0,0.2)")
    return fig
