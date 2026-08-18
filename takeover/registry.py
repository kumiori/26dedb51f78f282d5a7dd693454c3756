"""Registry interface plus a read-only local fallback for offline development."""

from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from .models import Entity, Necessity, Relation


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
        return [
            Necessity("need-abstract", "abstract", "application", "in_progress"),
            Necessity("need-material", "material", "application", "collecting"),
            Necessity("need-initial-kernel", "initial_kernel", "application", "found"),
            Necessity("need-photographs", "photographs", "application", "found"),
            Necessity("need-voices-sound", "voices_sound", "application", "agreed"),
            Necessity("need-translation", "translation", "application", "open"),
        ]

    def add_entity(self, entity: Entity) -> Entity:
        if any(item["id"] == entity.id for item in self._state["takeover_entities"]):
            raise ValueError(f"Entity id already exists: {entity.id}")
        self._state["takeover_entities"].append(asdict(entity))
        return entity
