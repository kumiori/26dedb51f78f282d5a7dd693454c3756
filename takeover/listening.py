"""Read-only boundary for the evolving suggested-listening field."""

from pathlib import Path
from typing import Any

import yaml


def load_listening(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "takeover-listening/v1":
        raise ValueError("Unsupported listening schema")
    listening = payload.get("suggested_listening")
    if not isinstance(listening, dict) or not isinstance(listening.get("items"), list):
        raise ValueError("Listening field must contain an items list")
    return payload
