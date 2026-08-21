"""Resource-state grammar and submission transition validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


RESOURCE_STATES = {"secured", "offered", "needed", "intention", "conditional", "open", "possible", "growing"}


def load_resource_field(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "takeover-resource-field/v1":
        raise ValueError("Expected a takeover-resource-field/v1 document.")
    application = payload.get("application") or {}
    state = application.get("state")
    submitted_at = application.get("submitted_at")
    if state not in {"open", "submitted"}:
        raise ValueError("Application state must be open or submitted.")
    if state == "submitted" and not submitted_at:
        raise ValueError("A submitted application requires its irreversible transition timestamp.")
    rows = payload.get("resources")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Resource field requires resource rows.")
    if any(row.get("state") not in RESOURCE_STATES for row in rows):
        raise ValueError("Unknown resource state.")
    return payload


def resource_rows(
    payload: dict[str, Any], *, active_people: int, bucket_bytes: int,
    bucket_files: int, activation_events: int,
) -> list[dict[str, Any]]:
    rows = []
    for source in payload["resources"]:
        row = dict(source)
        if row["id"] == "people":
            row["value"] = f"{active_people} ACTIVE"
        elif row["id"] == "storage":
            row["value"] = f"{bucket_bytes / 1024 / 1024:.2f} MB · {bucket_files} FILES" if bucket_bytes else f"0 B · {bucket_files} FILES"
        elif row["id"] == "attention":
            row["value"] = f"{activation_events} SESSION ACTIVATIONS" if activation_events else "GROWING"
        else:
            row["value"] = str(row.get("display") or row["state"]).upper()
        rows.append(row)
    return rows
