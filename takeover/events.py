"""Privacy-bounded session event stream for visible interface diagnostics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


EVENTS_KEY = "takeover_event_log"


def record_event(state: dict[str, Any], label_key: str, target: str = "", detail: str = "") -> dict[str, str]:
    event = {
        "occurred_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label_key": label_key,
        "target": str(target),
        "detail": str(detail),
    }
    state.setdefault(EVENTS_KEY, []).append(event)
    return event


def record_event_once(state: dict[str, Any], token: str, label_key: str, target: str = "", detail: str = "") -> bool:
    tokens = state.setdefault("takeover_event_tokens", set())
    if token not in tokens:
        tokens.add(token)
        record_event(state, label_key, target, detail)
        return True
    return False


def list_events(state: dict[str, Any]) -> list[dict[str, str]]:
    return list(state.get(EVENTS_KEY, []))
