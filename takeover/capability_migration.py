"""One-shot consolidation of legacy raw capabilities into player verifiers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping

from .node_population import PlayerPopulation
from .player_invitations import capability_verifier


class CapabilityMigrationError(ValueError):
    """Raised before writes when migration cannot preserve identity invariants."""


@dataclass(frozen=True)
class CapabilityMigrationReport:
    lines: tuple[str, ...]
    migrated: int
    verified: int
    skipped: int
    total: int


def _name_key(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _payload(row: dict[str, Any], metadata: dict[str, Any]) -> PlayerPopulation:
    return PlayerPopulation(
        player_id=str(row["player_id"]),
        name=str(row["name"]),
        label=str(row.get("label") or "Person • Alien"),
        image_url=str(row.get("image_url") or ""),
        bio=str(row.get("bio") or ""),
        practice=str(row.get("practice") or ""),
        sample_url=str(row.get("sample_url") or ""),
        metadata=metadata,
        initial_condition=dict(row.get("initial_condition") or {}),
        project_stage=str(row.get("project_stage") or "application"),
        node_stage=str(metadata.get("node_stage") or "node_population"),
        status=str(row.get("status") or "active"),
        network_state=str(row.get("network_state") or "active"),
        visibility=str(row.get("visibility") or "public"),
    )


def migrate_legacy_capabilities(
    store: Any,
    identities: Mapping[str, Mapping[str, Any]],
    *,
    mapping: Mapping[str, str] | None,
    clock: Callable[[], datetime],
) -> CapabilityMigrationReport:
    """Preflight, write, and verify legacy capabilities without exposing raw values."""
    rows = list(store.list_players())
    by_id: dict[str, list[dict[str, Any]]] = {}
    by_name: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_id.setdefault(str(row.get("player_id") or "").strip(), []).append(row)
        by_name.setdefault(_name_key(str(row.get("name") or "")), []).append(row)

    prepared: list[tuple[str, dict[str, Any], str, bool]] = []
    skipped_aliases: list[str] = []
    proposed: list[str] = []
    for alias, config in identities.items():
        raw = str(config.get("capability") or "").strip()
        if not raw:
            skipped_aliases.append(alias)
            continue
        explicit_person_id = str((mapping or {}).get(alias) or "").strip()
        person_id = explicit_person_id or alias
        matches = by_id.get(person_id, [])
        if not matches and not explicit_person_id:
            matches = by_name.get(_name_key(alias), [])
        if len(matches) != 1:
            reason = "missing player row" if not matches else "duplicate Person ID"
            raise CapabilityMigrationError(f"{alias}: {reason}")
        row = matches[0]
        if int(row.get("row_count") or 1) != 1 or store.count_players(str(row["player_id"])) != 1:
            raise CapabilityMigrationError(f"{alias}: duplicate Person ID")
        verifier = capability_verifier(raw)
        proposed.append(verifier)
        current = (row.get("metadata") or {}).get("capability") or {}
        current_verifier = str(current.get("verifier") or "")
        same = current_verifier == verifier and current.get("status") == "active"
        if current_verifier and current.get("status") == "active" and not same:
            raise CapabilityMigrationError(f"{alias}: different active verifier")
        prepared.append((alias, row, verifier, same))

    if any(count > 1 for count in Counter(proposed).values()):
        raise CapabilityMigrationError("duplicate capability verifier in migration input")
    existing = Counter(
        str(((row.get("metadata") or {}).get("capability") or {}).get("verifier") or "")
        for row in rows
    )
    for alias, row, verifier, same in prepared:
        owners_elsewhere = existing[verifier] - int(same)
        if owners_elsewhere:
            raise CapabilityMigrationError(f"{alias}: duplicate capability verifier")

    issued_at = clock()
    if issued_at.tzinfo is None or issued_at.utcoffset() is None:
        raise CapabilityMigrationError("migration clock must be timezone-aware")
    lines: list[str] = []
    migrated = 0
    verified = 0
    for alias, row, verifier, same in prepared:
        if same:
            verified += 1
            lines.append(f"{alias:<13}VERIFIED")
            continue
        metadata = dict(row.get("metadata") or {})
        metadata.pop("invitation_capability_hash", None)
        metadata["capability"] = {
            "version": 1,
            "algorithm": "sha256",
            "verifier": verifier,
            "status": "active",
            "issued_at": issued_at.isoformat(),
            "revoked_at": None,
        }
        store.upsert_player(_payload(row, metadata))
        readback = store.read_player(str(row["player_id"]))
        persisted = ((readback or {}).get("metadata") or {}).get("capability") or {}
        if persisted != metadata["capability"] or int((readback or {}).get("row_count") or 0) != 1:
            raise CapabilityMigrationError(f"{alias}: read-back verification failed")
        migrated += 1
        lines.append(f"{alias:<13}MIGRATED")
    lines.extend(
        f"{alias:<13}SKIPPED · NO LEGACY CAPABILITY"
        for alias in skipped_aliases
    )
    return CapabilityMigrationReport(
        tuple(lines), migrated, verified, len(skipped_aliases), len(identities)
    )
