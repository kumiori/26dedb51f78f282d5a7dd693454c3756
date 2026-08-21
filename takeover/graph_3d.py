"""Simple read-only 3D projection of the multiplex graph."""

from __future__ import annotations

from math import cos, pi, sin, sqrt

import plotly.graph_objects as go

from .models import Entity, Relation


def generated_3d_positions(entities: list[Entity]) -> dict[str, tuple[float, float, float]]:
    """Place nodes deterministically on a sphere without persisted coordinates."""
    ordered = sorted(entities, key=lambda item: item.id)
    count = len(ordered)
    positions: dict[str, tuple[float, float, float]] = {}
    golden_angle = pi * (3 - sqrt(5))
    for index, entity in enumerate(ordered):
        y = 1 - 2 * (index + .5) / max(1, count)
        radius = sqrt(max(0, 1 - y * y))
        angle = index * golden_angle
        positions[entity.id] = (radius * cos(angle), y, radius * sin(angle))
    return positions


def build_graph_3d_figure(entities: list[Entity], relations: list[Relation]) -> go.Figure:
    positions = generated_3d_positions(entities)
    status = {entity.id: entity.status for entity in entities}
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_z: list[float | None] = []
    for relation in relations:
        if relation.source not in positions or relation.target not in positions or relation.status != "active":
            continue
        source = positions[relation.source]
        target = positions[relation.target]
        edge_x.extend((source[0], target[0], None))
        edge_y.extend((source[1], target[1], None))
        edge_z.extend((source[2], target[2], None))

    colours = {
        "active": "#111111", "latent_known": "#777168",
        "latent_private": "#aaa6a0", "unknown": "#d2cec7",
    }
    figure = go.Figure()
    figure.add_trace(go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z, mode="lines",
        line={"color": "#777168", "width": 3}, hoverinfo="skip", name="relations",
    ))
    figure.add_trace(go.Scatter3d(
        x=[positions[item.id][0] for item in entities],
        y=[positions[item.id][1] for item in entities],
        z=[positions[item.id][2] for item in entities],
        mode="markers+text",
        text=[item.title if item.status in {"active", "latent_known"} else "" for item in entities],
        textposition="top center",
        customdata=[[item.id, item.status, item.type] for item in entities],
        hovertemplate="%{text}<br>%{customdata[1]} · %{customdata[2]}<extra></extra>",
        marker={
            "size": [13 if item.status == "active" else 9 for item in entities],
            "color": [colours.get(status[item.id], "#d2cec7") for item in entities],
            "line": {"color": "#45413d", "width": 1},
        },
        name="nodes",
    ))
    figure.update_layout(
        height=620,
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene={
            "bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"visible": False}, "yaxis": {"visible": False}, "zaxis": {"visible": False},
            "aspectmode": "cube",
            "camera": {"eye": {"x": 1.45, "y": 1.35, "z": .95}},
        },
    )
    if not entities:
        figure.add_annotation(text="NO NOTION NODES AVAILABLE", showarrow=False, x=.5, y=.5)
    return figure
