"""Registry interface plus a read-only local fallback for offline development."""

from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from .models import Entity, Necessity, Relation


NECESSITY_ROWS = (
    ("need-abstract", "abstract", "in_progress"),
    ("need-initial-kernel", "initial_kernel", "found"),
    ("need-material", "material", "collecting"),
    ("need-photographs", "photographs", "found"),
    ("need-translation", "translation", "open"),
    ("need-voices-sound", "voices_sound", "agreed"),
)


class Registry(Protocol):
    def list_entities(self) -> list[Entity]: ...
    def list_relations(self) -> list[Relation]: ...
    def list_necessities(self) -> list[Necessity]: ...
    def add_entity(self, entity: Entity) -> Entity: ...


class SessionRegistry:
    """Session-local test adapter. It never represents a public write path."""

    def __init__(self, state: dict) -> None:
        self._state = state
        state.setdefault("takeover_entities", [])
        state.setdefault("takeover_relations", [])

    def list_entities(self) -> list[Entity]:
        return [Entity(**item) for item in self._state["takeover_entities"]]

    def list_relations(self) -> list[Relation]:
        return [Relation(**item) for item in self._state["takeover_relations"]]

    def list_necessities(self) -> list[Necessity]:
        return [Necessity(item_id, name, "application", status) for item_id, name, status in NECESSITY_ROWS]

    def add_entity(self, entity: Entity) -> Entity:
        if any(item["id"] == entity.id for item in self._state["takeover_entities"]):
            raise ValueError(f"Entity id already exists: {entity.id}")
        self._state["takeover_entities"].append(asdict(entity))
        return entity
