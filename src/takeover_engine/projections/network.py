"""Interface-neutral network projection."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain import Entity, RegistryState, Relation


@dataclass(frozen=True, slots=True)
class NetworkProjection:
    nodes: tuple[Entity, ...]
    edges: tuple[Relation, ...]
    isolated_ids: tuple[str, ...]


def project_network(state: RegistryState, *, include_inactive: bool = False) -> NetworkProjection:
    nodes = state.entities if include_inactive else tuple(x for x in state.entities if x.status == "active")
    ids = {x.id for x in nodes}
    edges = tuple(x for x in state.relations if x.source in ids and x.target in ids and (include_inactive or x.status == "active"))
    connected = {endpoint for edge in edges for endpoint in (edge.source, edge.target)}
    return NetworkProjection(nodes, edges, tuple(x.id for x in nodes if x.id not in connected))
