"""Allocated resources and dimensionless intention impulses."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import yaml

from takeover.storage_timeline import storage_timeline


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
    field_x = allocation_x + event_x
    field_rows = [
        [_as_date(item["date"]).isoformat(), item["timing"], item.get("label", ""), "OBSERVED RESOURCE STATE"]
        for item in allocations
    ] + [
        [str(item.get("date") or ""), str(item.get("title") or ""), str(item.get("type") or "event"), "TRAJECTORY EVENT"]
        for item in dated_events
    ]
    figure.add_trace(go.Scatter(
        x=field_x,
        y=[0.0] * len(field_x),
        mode="lines+markers+text",
        name="BUCKET OF DOUGH",
        line={"color": "#111", "width": 3, "shape": "spline", "smoothing": 0.75},
        marker={"color": "#111", "size": [11] * len(allocations) + [8] * len(dated_events)},
        text=[item["timing"] for item in allocations] + [""] * len(dated_events),
        textposition="bottom center",
        textfont={"family": "Courier New, monospace", "size": 10, "color": "#111"},
        customdata=field_rows,
        hovertemplate="%{customdata[0]} · %{customdata[1]}<br>%{customdata[2]}<br>%{customdata[3]} · €%{y:.0f} ALLOCATED<extra></extra>",
    ))
    figure.add_annotation(
        x=allocation_x[0], y=0,
        text="D−2 · INCEPTION: THE MYTH OF THE CAVE",
        showarrow=False, xanchor="left", yshift=-52, align="left",
        font={"family": "Courier New, monospace", "size": 10, "color": "#111"},
    )

    # Intention has presence and timing, but no numeric magnitude or EUR value.
    impulse_x: list[float] = []
    impulse_custom: list[list[str]] = []
    for item in intentions:
        x = x_by_date[_as_date(item["date"])]
        impulse_x.append(x)
        impulse_custom.append([item["timing"], item["label"], "€0 ALLOCATED"])
    figure.add_trace(go.Scatter(
        x=impulse_x, y=[0.0] * len(impulse_x), mode="markers",
        name="INTENTION",
        marker={"color": "#315f78", "size": 22, "symbol": "diamond", "line": {"color": "#f5f2ed", "width": 2}},
        customdata=impulse_custom,
        hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>",
    ))
    figure.add_annotation(
        x=impulse_x[0], y=0,
        text="D−1 · INTENTION<br>NO ALLOCATED VALUE",
        showarrow=False, xanchor="left", xshift=14, yshift=-28, align="left",
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
            "title": "BUCKET OF DOUGH · EUR", "range": [-0.75, 0.45],
            "tickmode": "array", "tickvals": [0], "ticktext": ["€0"],
            "showgrid": False, "zeroline": True, "zerolinecolor": "rgba(17,17,17,.24)",
        },
        font={"family": "Courier New, monospace", "color": "#111"},
        legend={"orientation": "h", "x": 0, "y": 1.14, "font": {"size": 9}},
        hoverlabel={"font": {"family": "Courier New, monospace"}},
        shapes=[{
            "type": "line", "xref": "x", "yref": "y",
            "x0": event_x[-1] if event_x else allocation_x[-1], "x1": 1.04, "y0": 0, "y1": 0,
            "line": {"color": "rgba(17,17,17,.24)", "width": 3},
        }],
    )
    return figure


def build_bucket_figure(objects: list[dict[str, Any]]) -> go.Figure:
    """Plot one interpolated cumulative encrypted-volume line from observed metadata."""
    timeline = storage_timeline(objects)
    megabytes = [value / 1024 / 1024 for value in timeline["actual_bytes"]]
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=timeline["actual_times"], y=megabytes,
        mode="lines+markers", name="BUCKET OF GOLD",
        line={"color": "#111", "width": 3, "shape": "spline", "smoothing": 1.0},
        marker={"color": "#111", "size": 9},
        hovertemplate="%{x|%d %b %Y · %H:%M}<br>%{y:.3f} MB<extra></extra>",
    ))
    figure.update_layout(
        height=610, margin={"l": 65, "r": 65, "t": 90, "b": 70},
        paper_bgcolor="#f5f2ed", plot_bgcolor="#f5f2ed",
        title={"text": "Encrypted bucket", "x": 0, "font": {"family": "Courier New, monospace", "size": 19}},
        xaxis={"title": "OBSERVED TIME", "showgrid": False},
        yaxis={"title": "TOTAL VOLUME · MB", "rangemode": "tozero", "gridcolor": "rgba(17,17,17,.08)"},
        legend={"orientation": "h", "x": 0, "y": 1.14, "font": {"size": 9}},
        font={"family": "Courier New, monospace", "color": "#111"},
        hoverlabel={"font": {"family": "Courier New, monospace"}},
    )
    return figure


def build_combined_resources_figure(
    trajectory: dict[str, Any], resources: dict[str, Any], objects: list[dict[str, Any]],
    *, volume_scale: float = 1.0, now: datetime | None = None,
) -> go.Figure:
    """Combine resources and encrypted volume on one explicit scaled axis."""
    observed_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    allocations = resources["allocated_resources"]["observations"]
    events = sorted(
        (item for item in trajectory["primitives"] if item.get("date")),
        key=lambda item: str(item["date"]),
    )
    resource_dates = [str(item["date"]) for item in allocations] + [str(item["date"]) for item in events]
    resource_labels = [str(item["timing"]) for item in allocations] + [str(item.get("title") or "") for item in events]
    resource_kinds = ["OBSERVED RESOURCE STATE"] * len(allocations) + ["TRAJECTORY EVENT"] * len(events)

    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=resource_dates, y=[0.0] * len(resource_dates),
        mode="lines+markers", name="BUCKET OF DOUGH · €0",
        line={"color": "#111", "width": 3, "shape": "spline", "smoothing": 0.75},
        marker={"color": "#111", "size": [11] * len(allocations) + [8] * len(events)},
        customdata=[[label, kind] for label, kind in zip(resource_labels, resource_kinds)],
        hovertemplate="%{x|%d %b %Y}<br>%{customdata[0]}<br>%{customdata[1]} · €0 ALLOCATED<extra></extra>",
    ))

    for item in resources["investment_intentions"]:
        intention_date = str(item["date"])
        figure.add_trace(go.Scatter(
            x=[intention_date], y=[0.0], mode="markers",
            name="INTENTION",
            marker={"color": "#315f78", "size": 22, "symbol": "diamond", "line": {"color": "#f5f2ed", "width": 2}},
            customdata=[[item["timing"], item["label"]]],
            hovertemplate="%{x|%d %b %Y}<br>%{customdata[0]} · %{customdata[1]}<br>INTENTION · NO ALLOCATED VALUE<extra></extra>",
        ))

    storage = storage_timeline(objects, now=observed_now)
    beginning = min(
        datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        for value in resource_dates
    )
    horizon = observed_now + timedelta(days=5)
    scale_bytes = max(int(storage["actual_bytes"][-1]), 1)
    physical_megabytes = [value / 1024 / 1024 for value in storage["actual_bytes"]]
    scale = max(float(volume_scale), 0.01)
    scaled_volume = [scale * value / scale_bytes for value in storage["actual_bytes"]]
    figure.add_trace(go.Scatter(
        x=storage["actual_times"],
        y=scaled_volume,
        mode="lines+markers", name="BUCKET OF GOLD · V̂",
        line={"color": "#9f7860", "width": 3, "shape": "spline", "smoothing": 1.0},
        marker={"color": "#9f7860", "size": 9, "line": {"color": "#f5f2ed", "width": 1}},
        customdata=[[value] for value in physical_megabytes],
        hovertemplate="%{x|%d %b %Y · %H:%M}<br>V̂=%{y:.3f}<br>%{customdata[0]:.3f} MB<extra></extra>",
    ))

    figure.update_layout(
        height=420, margin={"l": 62, "r": 62, "t": 64, "b": 54},
        paper_bgcolor="#f5f2ed", plot_bgcolor="#f5f2ed",
        title={"text": "Resources / shared scale", "x": 0, "font": {"family": "Courier New, monospace", "size": 19, "color": "#111"}},
        xaxis={
            "title": {"text": "BEGINNING → NOW + 5 DAYS", "font": {"color": "#111"}},
            "range": [beginning, horizon],
            "tickfont": {"color": "#111"}, "showgrid": False, "zeroline": False,
        },
        yaxis={
            "title": {"text": "SHARED STATE SCALE", "font": {"color": "#111"}},
            "range": [-0.12 * max(1.0, scale), max(1.15, scale * 1.15)],
            "tickmode": "array", "tickvals": [0, scale],
            "ticktext": ["€0", f"V̂ₛ(now)={scale:g}"],
            "tickfont": {"color": "#111"},
            "showgrid": True, "gridcolor": "rgba(17,17,17,.08)",
            "zeroline": True, "zerolinecolor": "rgba(17,17,17,.28)",
        },
        legend={
            "orientation": "h", "x": 0, "y": 1.14,
            "font": {"family": "Courier New, monospace", "size": 10, "color": "#111"},
            "bgcolor": "rgba(245,242,237,.88)",
        },
        font={"family": "Courier New, monospace", "color": "#111"},
        hoverlabel={"font": {"family": "Courier New, monospace"}},
        hovermode="x unified",
    )
    return figure
