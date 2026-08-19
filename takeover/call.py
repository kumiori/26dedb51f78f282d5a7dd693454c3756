"""Validated source copy from the Fotografiska open call."""

from pathlib import Path
from typing import Any

import yaml


def load_call(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "takeover-call/v1":
        raise ValueError("Expected a takeover-call/v1 document.")
    if not isinstance(payload.get("paragraphs"), list) or not payload["paragraphs"]:
        raise ValueError("Call information requires at least one paragraph.")
    if not str(payload.get("emphasis") or "").strip():
        raise ValueError("Call information requires an emphasis statement.")
    return payload
