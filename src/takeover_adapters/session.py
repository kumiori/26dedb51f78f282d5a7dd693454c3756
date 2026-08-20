"""Session/dictionary adapters for development and interface integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import MutableMapping

from takeover_engine import Authority, Entity, Event, RegistryState


class SessionRegistry:
    """Provisional session-local registry; never an authoritative public store."""

    def __init__(self, state: MutableMapping[str, object]) -> None:
        self._state = state
        state.setdefault("takeover_entities", [])

    def read(self) -> RegistryState:
        rows = self._state.get("takeover_entities", [])
        return RegistryState(entities=tuple(Entity(**row) for row in rows), authority=Authority.PROVISIONAL, source="session")

    def add_entity(self, entity: Entity) -> Entity:
        rows = self._state["takeover_entities"]
        if any(row["id"] == entity.id for row in rows):
            raise ValueError(f"Entity id already exists: {entity.id}")
        data = asdict(entity)
        data["kind"] = entity.kind.value
        data["visibility"] = entity.visibility.value
        data["metadata"] = dict(entity.metadata)
        rows.append(data)
        return entity


class SessionEventSink:
    def __init__(self, state: MutableMapping[str, object], key: str = "takeover_events") -> None:
        self._state = state
        self._key = key
        state.setdefault(key, [])

    def append(self, event: Event) -> Event:
        self._state[self._key].append(event)
        return event

    def list(self) -> tuple[Event, ...]:
        return tuple(self._state[self._key])
