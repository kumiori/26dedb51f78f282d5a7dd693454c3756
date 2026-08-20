"""Validated domain records shared by TAKE OVER consumers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, TypeAlias

Scalar: TypeAlias = str | int | float | bool | None
Metadata: TypeAlias = Mapping[str, Scalar]


def _required(value: str, name: str) -> str:
    clean = str(value).strip()
    if not clean:
        raise ValueError(f"{name} is required")
    return clean


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


class Authority(StrEnum):
    AUTHORITATIVE = "authoritative"
    PROVISIONAL = "provisional"


class Visibility(StrEnum):
    PRIVATE = "private"
    PARTICIPANTS = "participants"
    PUBLIC = "public"


class EntityKind(StrEnum):
    PERSON = "person"
    PHOTOGRAPH = "photograph"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Identity:
    id: str
    display_name: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required(self.id, "identity id"))


@dataclass(frozen=True, slots=True)
class Capability:
    id: str
    action: str
    scope: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required(self.id, "capability id"))
        object.__setattr__(self, "action", _required(self.action, "capability action"))
        object.__setattr__(self, "scope", _required(self.scope, "capability scope"))


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    kind: EntityKind | str
    title: str
    label: str = ""
    stage: str = "application"
    status: str = "active"
    source: str = ""
    visibility: Visibility | str = Visibility.PUBLIC
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required(self.id, "entity id"))
        object.__setattr__(self, "title", _required(self.title, "entity title"))
        object.__setattr__(self, "kind", EntityKind(self.kind))
        object.__setattr__(self, "visibility", Visibility(self.visibility))
        object.__setattr__(self, "stage", _required(self.stage, "entity stage"))
        object.__setattr__(self, "status", _required(self.status, "entity status"))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def type(self) -> str:
        """Compatibility spelling for registry adapters."""
        return self.kind.value


@dataclass(frozen=True, slots=True)
class Relation:
    id: str
    source: str
    target: str
    kind: str
    stage: str = "application"
    status: str = "active"
    visibility: Visibility | str = Visibility.PUBLIC

    def __post_init__(self) -> None:
        for name in ("id", "source", "target", "kind", "stage", "status"):
            object.__setattr__(self, name, _required(getattr(self, name), f"relation {name}"))
        if self.source == self.target:
            raise ValueError("relation endpoints must differ")
        object.__setattr__(self, "visibility", Visibility(self.visibility))

    @property
    def type(self) -> str:
        return self.kind


@dataclass(frozen=True, slots=True)
class Necessity:
    id: str
    title: str
    stage: str
    status: str
    description: str = ""

    def __post_init__(self) -> None:
        for name in ("id", "title", "stage", "status"):
            object.__setattr__(self, name, _required(getattr(self, name), f"necessity {name}"))


@dataclass(frozen=True, slots=True)
class Event:
    id: str
    kind: str
    occurred_at: datetime
    actor_id: str = ""
    target_id: str = ""
    detail: str = ""
    visibility: Visibility | str = Visibility.PRIVATE

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required(self.id, "event id"))
        object.__setattr__(self, "kind", _required(self.kind, "event kind"))
        object.__setattr__(self, "occurred_at", _utc(self.occurred_at))
        object.__setattr__(self, "visibility", Visibility(self.visibility))


@dataclass(frozen=True, slots=True)
class RegistryState:
    entities: tuple[Entity, ...] = ()
    relations: tuple[Relation, ...] = ()
    necessities: tuple[Necessity, ...] = ()
    authority: Authority | str = Authority.PROVISIONAL
    source: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority", Authority(self.authority))
        for values, label in ((self.entities, "entity"), (self.relations, "relation"), (self.necessities, "necessity")):
            ids = [item.id for item in values]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate {label} identifiers")
        entity_ids = {item.id for item in self.entities}
        if any(row.source not in entity_ids or row.target not in entity_ids for row in self.relations):
            raise ValueError("relation endpoints must exist in registry state")
