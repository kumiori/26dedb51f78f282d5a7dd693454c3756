"""Stable public API for the TAKE OVER engine."""

from .domain import Authority, Capability, Entity, EntityKind, Event, Identity, Necessity, RegistryState, Relation, Visibility
from .operations import AppliedOverlay, Overlay, SystemClock, apply_overlay, emit_event, remove_overlay
from .projections import NetworkProjection, StoragePoint, project_events, project_network, project_storage
from .protocols import Clock, EventSink, Registry
from .schemas import Contribution, CryptoEnvelope, StorageObject

__version__ = "0.1.0"

__all__ = [
    "AppliedOverlay", "Authority", "Capability", "Clock", "Contribution", "CryptoEnvelope", "Entity",
    "EntityKind", "Event", "EventSink", "Identity", "Necessity", "NetworkProjection", "Overlay", "Registry",
    "RegistryState", "Relation", "StorageObject", "StoragePoint", "SystemClock", "Visibility", "apply_overlay",
    "emit_event", "project_events", "project_network", "project_storage", "remove_overlay",
]
