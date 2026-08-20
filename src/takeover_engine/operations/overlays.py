"""Reversible, idempotent temporary overlays."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain import Entity, Necessity, RegistryState, Relation


@dataclass(frozen=True, slots=True)
class Overlay:
    id: str
    entities: tuple[Entity, ...] = ()
    relations: tuple[Relation, ...] = ()
    necessities: tuple[Necessity, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("overlay id is required")


@dataclass(frozen=True, slots=True)
class AppliedOverlay:
    state: RegistryState
    overlay_id: str
    added_entity_ids: frozenset[str]
    added_relation_ids: frozenset[str]
    added_necessity_ids: frozenset[str]


def _missing(current: tuple, additions: tuple) -> tuple:
    identifiers = {item.id for item in current}
    return tuple(item for item in additions if item.id not in identifiers)


def apply_overlay(state: RegistryState, overlay: Overlay) -> AppliedOverlay:
    entities = _missing(state.entities, overlay.entities)
    relations = _missing(state.relations, overlay.relations)
    necessities = _missing(state.necessities, overlay.necessities)
    output = RegistryState(
        entities=(*state.entities, *entities),
        relations=(*state.relations, *relations),
        necessities=(*state.necessities, *necessities),
        authority=state.authority,
        source=state.source,
    )
    return AppliedOverlay(output, overlay.id, frozenset(x.id for x in entities), frozenset(x.id for x in relations), frozenset(x.id for x in necessities))


def remove_overlay(applied: AppliedOverlay) -> RegistryState:
    state = applied.state
    return RegistryState(
        entities=tuple(x for x in state.entities if x.id not in applied.added_entity_ids),
        relations=tuple(x for x in state.relations if x.id not in applied.added_relation_ids),
        necessities=tuple(x for x in state.necessities if x.id not in applied.added_necessity_ids),
        authority=state.authority,
        source=state.source,
    )
