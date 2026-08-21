"""Canonical participant-context registry for seeded node population."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path
import secrets
from typing import Any

import yaml

from .analytics import normalise_activation
from .models import Entity


def person_id_from_initial_condition(initial_condition: dict[str, str]) -> str:
    """Derive one stable ID from an immutable, canonical initial condition."""
    required = {"name", "t0", "origin", "nonce"}
    if set(initial_condition) != required:
        raise ValueError("Initial condition must contain exactly name, t0, origin, and nonce.")
    try:
        instant = datetime.fromisoformat(initial_condition["t0"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Initial condition t0 must be an ISO timestamp.") from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Initial condition t0 must include a timezone.")
    seed = {
        "name": " ".join(initial_condition["name"].strip().lower().split()),
        "nonce": initial_condition["nonce"].strip().lower(),
        "origin": initial_condition["origin"].strip().lower(),
        "t0": initial_condition["t0"],
    }
    if not all(seed.values()):
        raise ValueError("Initial condition values must be non-empty.")
    canonical = json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return f"player_{hashlib.sha256(canonical).hexdigest()[:16]}"


def make_person_id(canonical_name: str, created_at: str, *, nonce: str | None = None) -> tuple[str, dict[str, str]]:
    """Mint an ID and return the immutable initial condition that defines it."""
    initial_condition = {
        "name": " ".join(canonical_name.strip().lower().split()),
        "t0": created_at,
        "origin": "takeover",
        "nonce": (nonce or secrets.token_hex(8)).strip().lower(),
    }
    return person_id_from_initial_condition(initial_condition), initial_condition


@dataclass(frozen=True)
class PlayerPopulation:
    """Application-level payload for inhabiting one player node."""

    player_id: str
    name: str
    label: str = ""
    image_url: str = ""
    bio: str = ""
    practice: str = ""
    sample_url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    initial_condition: dict[str, str] = field(default_factory=dict)
    project_stage: str = "application"
    node_stage: str = "node_population"
    status: str = "active"
    network_state: str = "active"
    visibility: str = "public"

    def __post_init__(self) -> None:
        if not self.player_id.strip() or not self.name.strip():
            raise ValueError("Player ID and name are required.")
        if self.network_state not in {"active", "latent_known", "latent_private", "unknown"}:
            raise ValueError(f"Unsupported network state: {self.network_state}")
        if self.visibility not in {"public", "private", "anonymous"}:
            raise ValueError(f"Unsupported visibility: {self.visibility}")
        if self.initial_condition and person_id_from_initial_condition(self.initial_condition) != self.player_id:
            raise ValueError("Person ID does not match its initial condition.")
        if self.player_id.startswith("player_") and not self.initial_condition:
            raise ValueError("Generated player IDs require their initial condition.")


def upsert_player_verified(store: Any, payload: PlayerPopulation) -> dict[str, Any]:
    """Upsert one player and reject any incomplete or mismatched adapter read-back."""
    row = store.upsert_player(payload)
    checks = {
        "Person ID": row.get("player_id") == payload.player_id,
        "Image URL": row.get("image_url") == payload.image_url,
        "Bio": row.get("bio") == payload.bio,
        "Practice": row.get("practice") == payload.practice,
        "Sample URL": row.get("sample_url") == payload.sample_url,
        "Project Stage": row.get("project_stage") == payload.project_stage,
        "Status": row.get("status") == payload.status,
        "Node Stage": (row.get("metadata") or {}).get("node_stage") == payload.node_stage,
        "Unique Person ID": row.get("row_count") == 1,
    }
    failures = [label for label, passed in checks.items() if not passed]
    if failures:
        raise ValueError("Player read-back mismatch: " + ", ".join(failures))
    return row


def upsert_inhabited_node(
    store: Any,
    entity: Entity,
    *,
    image_url: str,
    bio: str,
    practice: str,
    sample_url: str,
    crop: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Persist an inhabited graph entity through the production player contract."""
    metadata = dict(entity.metadata)
    for projected_key in (
        "avatar", "bio", "practice", "sample_url", "registry_status", "visibility",
    ):
        metadata.pop(projected_key, None)
    if crop:
        metadata["avatar_crop"] = dict(crop)
    complete = bool(image_url.strip() and bio.strip() and practice.strip() and sample_url.strip())
    payload = PlayerPopulation(
        player_id=entity.id,
        name=entity.title,
        label=entity.label,
        image_url=image_url.strip(),
        bio=bio.strip(),
        practice=practice.strip(),
        sample_url=sample_url.strip(),
        metadata=metadata,
        initial_condition=dict(entity.metadata.get("initial_condition") or {}),
        project_stage=entity.stage,
        node_stage="ready" if complete else "node_population",
        status=str(entity.metadata.get("registry_status") or "active"),
        network_state=entity.status,
        visibility=str(entity.metadata.get("visibility") or "public"),
    )
    return upsert_player_verified(store, payload)


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
