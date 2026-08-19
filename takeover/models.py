"""Small typed boundary for the multiplex registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ENTITY_TYPES = ("person", "photograph", "audio")
STAGES = ("application", "activation", "production", "exhibition", "propagation")


def entity_type_label(entity_type: str) -> str:
    """Return the public ontology label without changing registry identifiers."""
    return "Person • Alien" if entity_type == "person" else entity_type.upper()


@dataclass(frozen=True)
class Entity:
    id: str
    type: str
    title: str
    label: str = ""
    stage: str = "application"
    status: str = "active"
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in ENTITY_TYPES:
            raise ValueError(f"Unsupported entity type: {self.type}")
        if self.stage not in STAGES:
            raise ValueError(f"Unsupported stage: {self.stage}")
        if not self.id.strip() or not self.title.strip():
            raise ValueError("Entity id and title are required.")


@dataclass(frozen=True)
class Relation:
    id: str
    source: str
    target: str
    type: str
    stage: str = "application"
    status: str = "active"


@dataclass(frozen=True)
class Necessity:
    id: str
    title: str
    stage: str
    status: str
    description: str = ""
