"""Canonical participant-context registry for seeded node population."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .analytics import normalise_activation


def load_population_registry(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text())
    if not isinstance(payload, dict) or payload.get("schema_version") != "takeover-node-population/v1":
        raise ValueError("Expected a takeover-node-population/v1 document.")
    rows = payload.get("participants")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Node population registry requires participants.")
    node_ids: set[str] = set()
    aliases: set[str] = set()
    for row in rows:
        node_id = str(row.get("node_id") or "").strip()
        row_aliases = [normalise_activation(item) for item in row.get("aliases") or []]
        if not node_id or node_id in node_ids or not row_aliases or any(not item or item in aliases for item in row_aliases):
            raise ValueError("Node population IDs and aliases must be non-empty and unique.")
        node_ids.add(node_id)
        aliases.update(row_aliases)
    return payload


def resolve_population_participant(payload: dict[str, Any], activation: str) -> str | None:
    candidate = normalise_activation(activation)
    matches = [
        str(row["node_id"])
        for row in payload["participants"]
        if candidate in {normalise_activation(item) for item in row["aliases"]}
    ]
    return matches[0] if len(matches) == 1 else None
