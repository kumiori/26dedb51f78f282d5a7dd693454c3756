"""Read-only M1 trajectory renderer adapted from app_protocol_hack semantics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import yaml


EVENT_TYPES = {
    "gateway": ("◇", "#9f7860"),
    "action": ("▲", "#ff2d0a"),
    "update": ("■", "#6f7774"),
    "milestone": ("▼", "#111111"),
    "share_resources": ("⇄", "#506b7a"),
    "event": ("●", "#111111"),
}


def load_trajectory(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "trajectory-plan/v2":
        raise ValueError("Expected a trajectory-plan/v2 document.")
    if not isinstance(payload.get("plan"), dict) or not isinstance(payload.get("primitives"), list):
        raise ValueError("Trajectory must contain plan and primitives.")
    return payload


def build_timeline_figure(payload: dict[str, Any]) -> go.Figure:
    plan = payload["plan"]
    events = sorted(payload["primitives"], key=lambda item: float(item.get("time_parameter", 0)))
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=[0, 1], y=[0, 0], mode="lines",
        line={"color": "rgba(16,16,16,.22)", "width": 1},
        hoverinfo="skip", showlegend=False,
    ))
    for index, event in enumerate(events):
        kind = str(event.get("type") or "event")
        glyph, color = EVENT_TYPES.get(kind, EVENT_TYPES["event"])
        x = float(event.get("time_parameter") or event.get("temporal_position") or 0)
        # Keep the primitive alternation, but stagger neighbouring labels enough
        # to prevent the application-stage cluster from colliding.
        tier = index % 4
        y = (0.13, -0.13, 0.23, -0.23)[tier]
        title = str(event.get("title") or kind.replace("_", " ").title())
        figure.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text",
            marker={"size": 18, "color": color, "line": {"color": "#f5f2ed", "width": 3}},
            text=[f"{glyph} {title}"], textposition="top center" if y > 0 else "bottom center",
            textfont={"family": "Courier New, monospace", "size": 10, "color": "#111"},
            customdata=[[kind, event.get("date", ""), event.get("visibility", "")]],
            hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
            showlegend=False,
        ))
        figure.add_shape(type="line", x0=x, x1=x, y0=0, y1=y, line={"color": "rgba(16,16,16,.25)", "width": 1})
    anchors = plan.get("qualitative_anchors") or []
    figure.update_layout(
        height=520,
        margin={"l": 35, "r": 35, "t": 70, "b": 55},
        paper_bgcolor="#f5f2ed", plot_bgcolor="#f5f2ed",
        title={"text": str(plan.get("title") or "Trajectory"), "x": 0, "font": {"family": "Courier New, monospace", "size": 19}},
        xaxis={
            "range": [-0.03, 1.03], "tickmode": "array",
            "tickvals": [float(item[1]) for item in anchors],
            "ticktext": [str(item[0]).upper() for item in anchors],
            "showgrid": False, "zeroline": False,
            "tickfont": {"family": "Courier New, monospace", "size": 10},
        },
        yaxis={"range": [-0.38, 0.38], "visible": False},
        font={"family": "Courier New, monospace", "color": "#111"},
        hoverlabel={"font": {"family": "Courier New, monospace"}},
    )
    return figure
