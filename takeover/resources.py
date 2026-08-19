"""Allocated resources and dimensionless intention impulses."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import yaml


def _as_date(value: Any) -> date:
    return datetime.fromisoformat(str(value)).date()


def load_resources(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "takeover-resources/v2":
        raise ValueError("Expected a takeover-resources/v2 document.")
    allocations = payload.get("allocated_resources", {}).get("observations")
    intentions = payload.get("investment_intentions")
    if not isinstance(allocations, list) or len(allocations) != 3:
        raise ValueError("Allocated resources require D−2, D−1 and D0 observations.")
    if [item.get("timing") for item in allocations] != ["D−2", "D−1", "D0"]:
        raise ValueError("Allocated resource observations must remain ordered D−2, D−1, D0.")
    if any(float(item.get("amount_eur", 0)) != 0 for item in allocations):
        raise ValueError("Initial allocated-resource observations must remain exactly zero.")
    if not isinstance(intentions, list) or not intentions:
        raise ValueError("At least one intention is required.")
    if any(float(item.get("amount_eur", 0)) != 0 for item in intentions):
        raise ValueError("Intention impulses must not encode allocated money.")
    return payload


def application_date(trajectory: dict[str, Any]) -> date:
    candidates = [
        event for event in trajectory["primitives"]
        if "send application" in str(event.get("title") or "").lower()
    ]
    if not candidates:
        raise ValueError("Trajectory has no dated Send application event.")
    return _as_date(candidates[0]["date"])


def build_resources_figure(trajectory: dict[str, Any], resources: dict[str, Any]) -> go.Figure:
    allocations = resources["allocated_resources"]["observations"]
    intentions = resources["investment_intentions"]
    events = sorted(trajectory["primitives"], key=lambda item: float(item.get("time_parameter", 0)))
    dated_events = [event for event in events if event.get("date")]

    allocation_x = [0.12, 0.24, 0.36]
    event_x = [0.58 + index * (0.40 / max(1, len(dated_events) - 1)) for index in range(len(dated_events))]
    x_by_date = {_as_date(item["date"]): x for x, item in zip(allocation_x, allocations)}

    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=allocation_x,
        y=[0.0, 0.0, 0.0],
        mode="lines+markers+text",
        name="ALLOCATED RESOURCES",
        line={"color": "#111", "width": 2},
        marker={"color": "#111", "size": 8},
        text=[item["timing"] for item in allocations],
        textposition="bottom center",
        textfont={"family": "Courier New, monospace", "size": 10, "color": "#111"},
        customdata=[[_as_date(item["date"]).isoformat(), item["timing"], item.get("label", "")] for item in allocations],
        hovertemplate="%{customdata[0]} · %{customdata[1]}<br>%{customdata[2]}<br>ALLOCATED · €%{y:.0f}<extra></extra>",
    ))
    figure.add_annotation(
        x=allocation_x[0], y=0,
        text="D−2 · INCEPTION: THE MYTH OF THE CAVE",
        showarrow=True, arrowhead=0, ax=40, ay=-65, align="left",
        font={"family": "Courier New, monospace", "size": 10, "color": "#111"},
    )

    # A Dirac-like impulse is drawn against a hidden, dimensionless axis. Its
    # height means concentration of intention, never euros; every source row
    # continues to carry amount_eur: 0.
    delta_x: list[float | None] = []
    delta_y: list[float | None] = []
    impulse_x: list[float] = []
    impulse_custom: list[list[str]] = []
    for item in intentions:
        x = x_by_date[_as_date(item["date"])]
        delta_x.extend([x, x, None])
        delta_y.extend([0.0, 1.0, None])
        impulse_x.append(x)
        impulse_custom.append([item["timing"], item["label"], "€0 ALLOCATED"])
    figure.add_trace(go.Scatter(
        x=delta_x, y=delta_y, yaxis="y2", mode="lines",
        name="INVESTMENT INTENTION · δ",
        line={"color": "#315f78", "width": 3},
        hoverinfo="skip",
    ))
    figure.add_trace(go.Scatter(
        x=impulse_x, y=[1.0] * len(impulse_x), yaxis="y2", mode="markers",
        name="INTENTION",
        marker={"color": "#315f78", "size": 14, "symbol": "diamond", "line": {"color": "#f5f2ed", "width": 2}},
        customdata=impulse_custom,
        hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>",
    ))
    figure.add_annotation(
        x=impulse_x[0], y=1.0, yref="y2",
        text="D−1 · INTENTION<br>CONCENTRATION OF INTENTION · €0",
        showarrow=True, arrowhead=0, ax=80, ay=-45, align="left",
        font={"family": "Courier New, monospace", "size": 10, "color": "#315f78"},
    )
    figure.update_layout(
        height=610, margin={"l": 75, "r": 35, "t": 90, "b": 90},
        paper_bgcolor="#f5f2ed", plot_bgcolor="#f5f2ed",
        title={"text": "Allocated resources (in EUR)", "x": 0, "font": {"family": "Courier New, monospace", "size": 19, "color": "#111"}},
        xaxis={
            "title": "INCEPTION → BEFORE THE LABELLED EVENTS",
            "range": [0.04, 1.04], "tickmode": "array", "tickvals": event_x,
            "ticktext": [str(event.get("title") or "") for event in dated_events],
            "tickangle": -28,
            "tickfont": {"family": "Courier New, monospace", "size": 9, "color": "#68635e"},
            "showgrid": False, "zeroline": False,
        },
        yaxis={
            "title": "ALLOCATED · EUR", "range": [-0.08, 0.32],
            "tickmode": "array", "tickvals": [0], "ticktext": ["€0"],
            "showgrid": False, "zeroline": True, "zerolinecolor": "rgba(17,17,17,.24)",
        },
        yaxis2={"overlaying": "y", "side": "right", "range": [0, 1.18], "visible": False, "fixedrange": True},
        font={"family": "Courier New, monospace", "color": "#111"},
        legend={"orientation": "h", "x": 0, "y": 1.14, "font": {"size": 9}},
        hoverlabel={"font": {"family": "Courier New, monospace"}},
    )
    return figure
