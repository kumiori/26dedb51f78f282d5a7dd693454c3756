"""Event creation independent of persistence and wall-clock time."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from ..domain import Event, Visibility
from ..protocols import Clock, EventSink


@dataclass(frozen=True, slots=True)
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def emit_event(
    sink: EventSink,
    clock: Clock,
    kind: str,
    *,
    event_id: str | None = None,
    actor_id: str = "",
    target_id: str = "",
    detail: str = "",
    visibility: Visibility = Visibility.PRIVATE,
) -> Event:
    return sink.append(Event(event_id or uuid4().hex, kind, clock.now(), actor_id, target_id, detail, visibility))
