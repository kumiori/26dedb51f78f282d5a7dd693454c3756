"""Read-only temporal and multiplex analysis of the Takeover graph."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import networkx as nx
import plotly.graph_objects as go

from .graph_3d import generated_3d_positions
from .models import Entity, Relation


LAYER_COLOURS = ("#ff4b1f", "#315f78", "#6c5ce7", "#008f7a", "#b26a00", "#777168")


def _instant(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo and parsed.utcoffset() is not None else None


def connectivity_history(
    entities: list[Entity],
    relations: list[Relation],
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return cumulative observed registry connectivity at each known timestamp."""
    current = now or datetime.now(timezone.utc)
    entity_times = {item.id: _instant(item.metadata.get("created_at")) for item in entities}
    relation_times = {item.id: _instant(item.metadata.get("created_at")) for item in relations}
    observed = sorted({value for value in (*entity_times.values(), *relation_times.values()) if value})
    if not observed:
        node_count = len(entities)
        edge_count = sum(
            item.status == "active" and item.source in entity_times and item.target in entity_times
            for item in relations
        )
        return [{
            "timestamp": current,
            "nodes": node_count,
            "relations": edge_count,
            "connectivity": (1 + edge_count) / node_count if node_count else 0.0,
            "density": edge_count / (node_count * (node_count - 1)) if node_count > 1 else 0.0,
            "basis": "current snapshot; creation history unavailable",
        }]
    instants = [*observed, current] if current > observed[-1] else observed
    rows: list[dict[str, Any]] = []
    for instant in instants:
        present = {
            item.id for item in entities
            if entity_times[item.id] is None or entity_times[item.id] <= instant
        }
        edges = sum(
            item.status == "active"
            and item.source in present
            and item.target in present
            and (relation_times[item.id] is None or relation_times[item.id] <= instant)
            for item in relations
        )
        count = len(present)
        rows.append({
            "timestamp": instant,
            "nodes": count,
            "relations": edges,
            "connectivity": (1 + edges) / count if count else 0.0,
            "density": edges / (count * (count - 1)) if count > 1 else 0.0,
            "basis": "cumulative Created At observations",
        })
    return rows


def connectivity_figure(rows: list[dict[str, Any]]) -> go.Figure:
    figure = go.Figure(go.Scatter(
        x=[row["timestamp"] for row in rows],
        y=[row["connectivity"] for row in rows],
        mode="lines+markers",
        line={"color": "#111111", "width": 2},
        marker={"color": "#ff4b1f", "size": 7},
        customdata=[[row["nodes"], row["relations"], row["density"]] for row in rows],
        hovertemplate="%{x}<br>connectivity %{y:.3f}<br>%{customdata[0]} nodes · %{customdata[1]} relations<br>directed density %{customdata[2]:.3f}<extra></extra>",
        name="connectivity",
    ))
    figure.update_layout(
        height=240,
        margin={"l": 10, "r": 10, "t": 25, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis={"title": "OBSERVED TIME", "showgrid": False},
        yaxis={"title": "(1 + M) / N", "rangemode": "tozero", "gridcolor": "rgba(0,0,0,.12)"},
    )
    return figure


def multiplex_statistics(entities: list[Entity], relations: list[Relation]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ids = {item.id for item in entities}
    valid = [item for item in relations if item.status == "active" and item.source in ids and item.target in ids]
    graph = nx.DiGraph()
    graph.add_nodes_from(ids)
    graph.add_edges_from((item.source, item.target) for item in valid)
    undirected = graph.to_undirected()
    reciprocity = nx.reciprocity(graph) if graph.number_of_edges() else 0.0
    layer_names = {item.type for item in valid}
    dyad_layers: dict[tuple[str, str], set[str]] = defaultdict(set)
    node_layers: dict[str, set[str]] = defaultdict(set)
    for item in valid:
        dyad_layers[(item.source, item.target)].add(item.type)
        node_layers[item.source].add(item.type)
        node_layers[item.target].add(item.type)
    global_metrics = {
        "nodes": graph.number_of_nodes(),
        "relations": len(valid),
        "layers": len({item.type for item in valid}),
        "directed_density": nx.density(graph),
        "mean_total_degree": (2 * len(valid) / len(ids)) if ids else 0.0,
        "isolates": nx.number_of_isolates(graph),
        "weak_components": nx.number_weakly_connected_components(graph) if ids else 0,
        "reciprocity": float(reciprocity or 0.0),
        "transitivity": nx.transitivity(undirected),
        "mean_clustering": nx.average_clustering(undirected) if ids else 0.0,
        "mean_layers_per_dyad": (
            sum(len(value) for value in dyad_layers.values()) / len(dyad_layers)
            if dyad_layers else 0.0
        ),
        "mean_node_layer_participation": (
            sum(len(node_layers[node]) / len(layer_names) for node in ids) / len(ids)
            if ids and layer_names else 0.0
        ),
    }
    grouped: dict[str, list[Relation]] = defaultdict(list)
    for relation in valid:
        grouped[relation.type].append(relation)
    layers: list[dict[str, Any]] = []
    for layer, edges in sorted(grouped.items()):
        layer_graph = nx.DiGraph()
        layer_graph.add_nodes_from(ids)
        layer_graph.add_edges_from((item.source, item.target) for item in edges)
        participants = {endpoint for item in edges for endpoint in (item.source, item.target)}
        layers.append({
            "layer": layer,
            "relations": len(edges),
            "participating_nodes": len(participants),
            "directed_density": nx.density(layer_graph),
            "isolates": nx.number_of_isolates(layer_graph),
            "weak_components": nx.number_weakly_connected_components(layer_graph) if ids else 0,
            "reciprocity": float(nx.reciprocity(layer_graph) or 0.0) if edges else 0.0,
        })
    return global_metrics, layers


def multiplex_3d_figure(entities: list[Entity], relations: list[Relation]) -> go.Figure:
    positions = generated_3d_positions(entities)
    layers = sorted({item.type for item in relations if item.status == "active"}) or ["no_relations"]
    figure = go.Figure()
    for layer_index, layer in enumerate(layers):
        z = float(layer_index)
        colour = LAYER_COLOURS[layer_index % len(LAYER_COLOURS)]
        edges = [item for item in relations if item.status == "active" and item.type == layer and item.source in positions and item.target in positions]
        edge_x: list[float | None] = []
        edge_y: list[float | None] = []
        edge_z: list[float | None] = []
        edge_text: list[str | None] = []
        for edge in edges:
            edge_x.extend((positions[edge.source][0], positions[edge.target][0], None))
            edge_y.extend((positions[edge.source][1], positions[edge.target][1], None))
            edge_z.extend((z, z, None))
            label = f"{edge.source} → {edge.type} → {edge.target}"
            edge_text.extend((label, label, None))
        figure.add_trace(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z, mode="lines",
            line={"color": colour, "width": 5}, name=f"{layer} · relations",
            text=edge_text,
            hovertemplate="%{text}<extra></extra>",
        ))
        figure.add_trace(go.Scatter3d(
            x=[positions[item.id][0] for item in entities],
            y=[positions[item.id][1] for item in entities],
            z=[z] * len(entities),
            mode="markers+text",
            text=[item.title if item.status in {"active", "latent_known"} else "" for item in entities],
            textposition="top center",
            customdata=[[item.id, item.status, item.type, layer] for item in entities],
            hovertemplate="%{text}<br>%{customdata[1]} · %{customdata[2]}<br>layer · %{customdata[3]}<extra></extra>",
            marker={"size": [10 if item.status == "active" else 6 for item in entities], "color": colour, "opacity": .82},
            name=f"{layer} · nodes",
        ))
    figure.update_layout(
        height=700, margin={"l": 0, "r": 0, "t": 30, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
        scene={
            "bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"visible": False}, "yaxis": {"visible": False},
            "zaxis": {"title": "RELATION LAYER", "tickvals": list(range(len(layers))), "ticktext": layers},
            "aspectmode": "manual", "aspectratio": {"x": 1, "y": 1, "z": max(.35, len(layers) * .28)},
        },
    )
    return figure
