"""Read-only scientific test surface for the current multiplex registry."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from takeover.database_status import inspect_registry
from takeover.network_analysis import (
    connectivity_figure,
    connectivity_history,
    multiplex_3d_figure,
    multiplex_statistics,
)
from takeover.registry import SessionRegistry


ROOT = Path(__file__).resolve().parents[1]


def notion_token() -> str:
    token = os.getenv("NOTION_TOKEN", "").strip()
    if token:
        return token
    try:
        notion = st.secrets.get("notion", {})
        return str(
            st.secrets.get("NOTION_TOKEN", "")
            or notion.get("token")
            or notion.get("api_key")
            or ""
        ).strip()
    except (KeyError, TypeError, AttributeError):
        return ""


st.set_page_config(page_title="TAKE OVER · Multiplex Network Analysis", page_icon="+", layout="wide")
st.title("MULTIPLEX NETWORK ANALYSIS / TEST")
st.caption("READ ONLY · GENERATED POSITIONS · OBSERVED REGISTRY DATA · NO CAUSAL CLAIMS")

token = notion_token()
if token:
    from takeover.notion import NotionRegistry

    repo = NotionRegistry(token, ROOT / "config" / "takeover_notion.json")
    mode = "notion"
else:
    repo = SessionRegistry(st.session_state)
    mode = "session"

diagnostics = inspect_registry(repo, mode)
entities = list(diagnostics.entities)
relations = list(diagnostics.relations)
if diagnostics.status == "error":
    st.error(f"PLAYER REGISTRY DEGRADED · {diagnostics.error_type}")
    st.stop()
if mode != "notion":
    st.warning("PLAYER REGISTRY UNAVAILABLE · SHOWING A PROVISIONAL SESSION SNAPSHOT")

summary, layer_rows = multiplex_statistics(entities, relations)
metrics = st.columns(6)
for column, (label, value) in zip(metrics, (
    ("NODES", summary["nodes"]),
    ("RELATIONS", summary["relations"]),
    ("LAYERS", summary["layers"]),
    ("DIRECTED DENSITY", f'{summary["directed_density"]:.3f}'),
    ("ISOLATES", summary["isolates"]),
    ("WEAK COMPONENTS", summary["weak_components"]),
), strict=True):
    column.metric(label, value)

st.subheader("LAYER-SEPARATED 3D PROJECTION")
st.caption(
    "Each horizontal level is one relation type. Nodes are repeated across layers to preserve player identity; "
    "coloured intralayer edges retain their relation labels. Position is generated and has no geographic meaning."
)
st.plotly_chart(
    multiplex_3d_figure(entities, relations),
    width="stretch",
    theme=None,
    config={"displayModeBar": True, "scrollZoom": True},
)

left, right = st.columns([1.15, .85], gap="large")
with left:
    st.subheader("CONNECTIVITY / OBSERVED TIME")
    history = connectivity_history(entities, relations)
    st.plotly_chart(connectivity_figure(history), width="stretch", theme=None, config={"displayModeBar": False})
    st.caption(history[-1]["basis"].upper())
with right:
    st.subheader("GLOBAL STRUCTURE")
    st.dataframe([
        {"metric": "mean total degree", "value": summary["mean_total_degree"]},
        {"metric": "reciprocity", "value": summary["reciprocity"]},
        {"metric": "transitivity", "value": summary["transitivity"]},
        {"metric": "mean clustering / undirected projection", "value": summary["mean_clustering"]},
        {"metric": "mean relation layers per directed dyad", "value": summary["mean_layers_per_dyad"]},
        {"metric": "mean node layer participation", "value": summary["mean_node_layer_participation"]},
    ], hide_index=True, width="stretch")

st.subheader("RELATION LAYERS")
if layer_rows:
    st.dataframe(layer_rows, hide_index=True, width="stretch")
else:
    st.info("NO ACTIVE RELATION LAYERS")

st.subheader("LABELLED RELATIONS")
titles = {item.id: item.title for item in entities}
relation_rows = [{
    "source": titles.get(item.source, item.source),
    "relation / layer": item.type,
    "target": titles.get(item.target, item.target),
    "project stage": item.stage,
    "status": item.status,
    "created at": item.metadata.get("created_at", "timestamp unavailable"),
} for item in relations]
st.dataframe(relation_rows, hide_index=True, width="stretch")

with st.expander("METHOD / INTERPRETATION", expanded=True):
    st.markdown(
        """
- The registry is treated as a **directed multiplex graph**: players/entities are nodes and each relation type is a layer.
- Density, reciprocity and weak components use the directed simple projection; parallel relations are retained in the layer table.
- Clustering and transitivity use an explicitly labelled undirected projection because directed clustering is unstable at this size.
- Isolates remain part of the graph. Small node and edge counts make all metrics descriptive, not inferential.
- The temporal curve is cumulative from available `Created At` values. Undated records are treated as present at the first observation and are not assigned invented dates.
"""
    )
