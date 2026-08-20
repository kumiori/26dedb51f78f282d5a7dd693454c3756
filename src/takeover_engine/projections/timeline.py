"""Interface-neutral chronological event projection."""

from __future__ import annotations

from ..domain import Event, Visibility


def project_events(events: tuple[Event, ...], *, visible: frozenset[Visibility] | None = None) -> tuple[Event, ...]:
    allowed = visible or frozenset(Visibility)
    return tuple(sorted((event for event in events if event.visibility in allowed), key=lambda event: (event.occurred_at, event.id)))
