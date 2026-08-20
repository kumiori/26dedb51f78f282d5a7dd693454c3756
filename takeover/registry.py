"""Registry interface plus a read-only local fallback for offline development."""

from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from .models import Entity, Necessity, Relation
from takeover_engine import Entity as EngineEntity
from takeover_engine import Overlay, RegistryState, Relation as EngineRelation, apply_overlay


NECESSITY_ROWS = (
    ("need-abstract", "abstract", "application", "in_progress"),
    ("need-initial-kernel", "initial_kernel", "application", "found"),
    ("need-material", "material", "application", "collecting"),
    ("need-photographs", "photographs", "application", "found"),
    ("need-translation", "translation", "application", "open"),
    ("need-voices-sound", "voices_sound", "application", "agreed"),
    ("need-application", "application", "application", "to_submit"),
    ("need-production", "production", "production", "not_yet_activated"),
)


# RC0's depth-structured social field is code-owned until the public
# contribution flow opens. Depth is semantic: 0 foreground, 1 latent known,
# 2 latent private, 3 unknown.
SEED_ENTITIES = (
    Entity("kumiori", "person", "KUMIORI", "Person • Alien / initiator / application", metadata={"display_name": "Andrés", "depth": 0}),
    Entity("ave", "person", "Ave", "Person • Alien / artist / application", metadata={"depth": 0}),
    Entity("mai_brit", "person", "Mai-Brit", "Person • Alien / voice / application", metadata={"depth": 0}),
    Entity("kenneerik", "person", "Kenn-Eerik", "Person • Alien / sound / application", metadata={"depth": 0}),
)
PRESEED_ENTITIES = (
    Entity("graziano", "person", "Graziano", "Person • Alien / potential / application", status="latent_known", metadata={"depth": 1}),
    Entity("michela", "person", "Michela", status="latent_private", metadata={"internal_name": "Michela", "depth": 2}),
    Entity("latent_01", "person", "latent_01", status="unknown", metadata={"depth": 3}),
    Entity("latent_02", "person", "latent_02", status="unknown", metadata={"depth": 3}),
)
SEED_RELATIONS = (
    Relation("seed-kumiori-ave", "kumiori", "ave", "collaborates_with"),
    Relation("seed-kumiori-mai-brit", "kumiori", "mai_brit", "collaborates_with"),
    Relation("seed-kumiori-kenneerik", "kumiori", "kenneerik", "collaborates_with"),
    Relation("seed-ave-kenneerik", "ave", "kenneerik", "collaborates_with"),
)


def with_rc0_seeds(
    entities: list[Entity], relations: list[Relation]
) -> tuple[list[Entity], list[Relation]]:
    """Apply the RC0 payload through the package's generic overlay operation."""
    def to_engine_entity(item: Entity) -> EngineEntity:
        return EngineEntity(item.id, item.type, item.title, item.label, item.stage, item.status, item.source, metadata=item.metadata)

    def to_engine_relation(item: Relation) -> EngineRelation:
        return EngineRelation(item.id, item.source, item.target, item.type, item.stage, item.status)

    # Some legacy adapters can return a partial fixture containing an edge
    # before both endpoints. Complete only those referenced endpoints from the
    # application seed so the validated engine state never contains a dangling
    # relation.
    source_entities = list(entities)
    source_ids = {item.id for item in source_entities}
    referenced_ids = {endpoint for item in relations for endpoint in (item.source, item.target)}
    seed_by_id = {item.id: item for item in (*SEED_ENTITIES, *PRESEED_ENTITIES)}
    source_entities.extend(seed_by_id[item_id] for item_id in referenced_ids - source_ids if item_id in seed_by_id)
    state = RegistryState(
        entities=tuple(to_engine_entity(item) for item in source_entities),
        relations=tuple(to_engine_relation(item) for item in relations),
    )
    overlay = Overlay(
        id="fotografiska-rc0",
        entities=tuple(to_engine_entity(item) for item in (*SEED_ENTITIES, *PRESEED_ENTITIES)),
        relations=tuple(to_engine_relation(item) for item in SEED_RELATIONS),
    )
    applied = apply_overlay(state, overlay).state
    return (
        [Entity(item.id, item.type, item.title, item.label, item.stage, item.status, item.source, dict(item.metadata)) for item in applied.entities],
        [Relation(item.id, item.source, item.target, item.type, item.stage, item.status) for item in applied.relations],
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
        return [Necessity(item_id, name, stage, status) for item_id, name, stage, status in NECESSITY_ROWS]

    def add_entity(self, entity: Entity) -> Entity:
        if any(item["id"] == entity.id for item in self._state["takeover_entities"]):
            raise ValueError(f"Entity id already exists: {entity.id}")
        self._state["takeover_entities"].append(asdict(entity))
        return entity
