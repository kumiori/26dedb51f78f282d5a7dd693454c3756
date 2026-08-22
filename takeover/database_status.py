"""Safe, read-only registry diagnostics for application interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from typing import Callable

from .models import Entity, Relation


@dataclass(frozen=True)
class RegistryDiagnostics:
    mode: str
    authority: str
    status: str
    entities: tuple[Entity, ...] = ()
    relations: tuple[Relation, ...] = ()
    error_type: str = ""

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def relation_count(self) -> int:
        return len(self.relations)


@dataclass(frozen=True)
class FactoryHealth:
    notion: str
    storage: str
    schema: str
    duplicate_person_ids: int = 0
    duplicate_capability_owners: int = 0
    duplicate_invitation_requests: int = 0
    error_type: str = ""


def inspect_registry(repo, mode: str) -> RegistryDiagnostics:
    """Read graph topology once and expose no provider error detail or secrets."""
    authority = "authoritative" if mode == "notion" else "provisional"
    try:
        entities = tuple(repo.list_entities())
        relations = tuple(repo.list_relations())
    except Exception as exc:
        return RegistryDiagnostics(
            mode=mode,
            authority=authority,
            status="error",
            error_type=type(exc).__name__,
        )
    return RegistryDiagnostics(
        mode=mode,
        authority=authority,
        status="connected" if entities or relations else "empty",
        entities=entities,
        relations=relations,
    )


def _duplicate_value_count(values: list[str]) -> int:
    return sum(count > 1 for count in Counter(value for value in values if value).values())


def inspect_factory_health(
    repo,
    mode: str,
    *,
    storage_probe: Callable[[], bool] | None = None,
) -> FactoryHealth:
    """Return safe factory-level health and recovery counts without identifiers."""
    try:
        players = list(repo.list_players())
        schema_probe = getattr(repo, "factory_schema_diagnostics", None)
        schema_result = schema_probe() if callable(schema_probe) else {"compatible": False}
    except Exception as exc:
        return FactoryHealth(
            notion="error" if mode == "notion" else "provisional",
            storage="not_checked",
            schema="error",
            error_type=type(exc).__name__,
        )
    if storage_probe is None:
        storage = "not_configured"
    else:
        try:
            storage = "reachable" if storage_probe() else "unreachable"
        except Exception:
            storage = "unreachable"
    metadata = [dict(row.get("metadata") or {}) for row in players]
    return FactoryHealth(
        notion="reachable" if mode == "notion" else "provisional",
        storage=storage,
        schema="compatible" if schema_result.get("compatible") else "incompatible",
        duplicate_person_ids=_duplicate_value_count([
            str(row.get("player_id") or "") for row in players
        ]),
        duplicate_capability_owners=_duplicate_value_count([
            str((item.get("capability") or {}).get("verifier") or "")
            for item in metadata
        ]),
        duplicate_invitation_requests=_duplicate_value_count([
            str(item.get("invitation_request_id") or "") for item in metadata
        ]),
    )
