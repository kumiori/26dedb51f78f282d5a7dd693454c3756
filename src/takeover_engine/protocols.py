"""Explicit extension protocols for state, time, and events."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .domain import Entity, Event, RegistryState


class Registry(Protocol):
    def read(self) -> RegistryState: ...
    def add_entity(self, entity: Entity) -> Entity: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class EventSink(Protocol):
    def append(self, event: Event) -> Event: ...
    def list(self) -> tuple[Event, ...]: ...
