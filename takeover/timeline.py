"""Read-only M1 trajectory renderer adapted from app_protocol_hack semantics."""

from __future__ import annotations

from pathlib import Path
from datetime import date, datetime
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


def build_time_mapping_figure(payload: dict[str, Any]) -> go.Figure:
    """Tentatively map calendar-linear time u onto qualitative time q=f(u)."""
    rows = build_time_mapping_rows(payload)

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="IDENTITY · q=u", line={"color": "rgba(17,17,17,.25)", "dash": "dot"}))
    figure.add_trace(go.Scatter(
        x=[row["linear"] for row in rows], y=[row["nonlinear"] for row in rows],
        mode="lines+markers", name="TENTATIVE MAP · q=f(u)",
        line={"color": "#315f78", "width": 2}, marker={"color": "#315f78", "size": 9},
        customdata=[[row["title"], row["residual"]] for row in rows],
        hovertemplate="%{customdata[0]}<br>u=%{x:.3f}<br>q=%{y:.3f}<br>Δ=%{customdata[1]:+.3f}<extra></extra>",
    ))
    figure.update_layout(
        height=430, margin={"l": 65, "r": 35, "t": 70, "b": 60},
        paper_bgcolor="#f5f2ed", plot_bgcolor="#f5f2ed",
        title={"text": "LINEAR ↔ NONLINEAR TIME", "x": 0, "font": {"family": "Courier New, monospace", "size": 18}},
        xaxis={"title": "u = (date − start) / horizon", "range": [-.03, 1.03], "showgrid": True, "gridcolor": "rgba(17,17,17,.08)"},
        yaxis={"title": "q = qualitative position", "range": [-.03, 1.03], "showgrid": True, "gridcolor": "rgba(17,17,17,.08)"},
        legend={"orientation": "h", "y": 1.12, "x": 0}, font={"family": "Courier New, monospace", "color": "#111"},
    )
    return figure


def build_time_mapping_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the dated event dataset used by the tentative time map."""
    plan = payload["plan"]
    start = date.fromisoformat(str(plan["start_date"]))
    end = start.fromordinal(start.toordinal() + int(plan.get("horizon_days") or 365))
    duration = max(1, (end - start).days)
    rows = []
    for event in payload["primitives"]:
        if not event.get("date"):
            continue
        event_date = datetime.fromisoformat(str(event["date"])).date()
        linear = (event_date - start).days / duration
        nonlinear = float(event.get("time_parameter") or event.get("temporal_position") or 0)
        rows.append({
            "date": str(event["date"]),
            "title": str(event.get("title") or ""),
            "type": str(event.get("type") or "event"),
            "linear": linear,
            "nonlinear": nonlinear,
            "residual": nonlinear - linear,
            "visibility": str(event.get("visibility") or ""),
        })
    rows.sort(key=lambda item: item["linear"])
    return rows
