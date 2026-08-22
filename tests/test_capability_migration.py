from datetime import datetime, timezone

import pytest

from takeover.capability_migration import CapabilityMigrationError, migrate_legacy_capabilities
from takeover.node_population import PlayerPopulation
from takeover.player_invitations import capability_verifier


class MemoryPlayers:
    def __init__(self, rows):
        self.rows = {row["player_id"]: dict(row) for row in rows}
        self.writes = 0

    def list_players(self):
        return list(self.rows.values())

    def count_players(self, person_id):
        return sum(row["player_id"] == person_id for row in self.rows.values())

    def upsert_player(self, payload: PlayerPopulation):
        self.writes += 1
        current = self.rows[payload.player_id]
        current["metadata"] = {**payload.metadata, "node_stage": payload.node_stage}
        current["row_count"] = 1
        return current

    def read_player(self, person_id):
        return self.rows.get(person_id)


def player(person_id, name, metadata=None):
    return {
        "player_id": person_id, "name": name, "label": "Person • Alien",
        "image_url": "", "bio": "", "practice": "", "sample_url": "",
        "metadata": metadata or {"node_stage": "node_population"},
        "initial_condition": {}, "project_stage": "application", "status": "active",
        "network_state": "active", "visibility": "public", "row_count": 1,
    }


def test_legacy_capability_migration_writes_structured_verifiers_and_is_idempotent() -> None:
    store = MemoryPlayers([player("ave-id", "Ave"), player("mai-id", "Mai-Brit")])
    identities = {
        "ave": {"capability": "ave-raw-secret"},
        "mai_brit": {"capability": "mai-raw-secret"},
    }
    mapping = {"ave": "ave-id", "mai_brit": "mai-id"}
    def clock():
        return datetime(2026, 8, 21, 22, tzinfo=timezone.utc)

    report = migrate_legacy_capabilities(store, identities, mapping=mapping, clock=clock)

    assert report.lines == ("ave          MIGRATED", "mai_brit     MIGRATED")
    assert report.migrated == 2
    assert store.rows["ave-id"]["metadata"]["capability"] == {
        "version": 1,
        "algorithm": "sha256",
        "verifier": capability_verifier("ave-raw-secret"),
        "status": "active",
        "issued_at": "2026-08-21T22:00:00+00:00",
        "revoked_at": None,
    }

    repeated = migrate_legacy_capabilities(store, identities, mapping=mapping, clock=clock)
    assert repeated.lines == ("ave          VERIFIED", "mai_brit     VERIFIED")
    assert store.writes == 2


def test_migration_refuses_conflicts_before_any_write() -> None:
    store = MemoryPlayers([
        player("ave-id", "Ave", {"capability": {
            "version": 1, "algorithm": "sha256", "verifier": "different",
            "status": "active", "issued_at": "earlier", "revoked_at": None,
        }}),
        player("mai-id", "Mai-Brit"),
    ])

    with pytest.raises(CapabilityMigrationError, match="active verifier"):
        migrate_legacy_capabilities(
            store,
            {"ave": {"capability": "ave-raw"}, "mai_brit": {"capability": "mai-raw"}},
            mapping={"ave": "ave-id", "mai_brit": "mai-id"},
            clock=lambda: datetime(2026, 8, 21, 22, tzinfo=timezone.utc),
        )

    assert store.writes == 0


def test_partial_mapping_falls_back_to_one_unique_player_name() -> None:
    store = MemoryPlayers([player("ave-generated-id", "Ave"), player("maibrit", "Mai-Brit")])

    report = migrate_legacy_capabilities(
        store,
        {
            "ave": {"capability": "ave-private-capability"},
            "mai_brit": {"capability": "mai-private-capability"},
        },
        mapping={"mai_brit": "maibrit"},
        clock=lambda: datetime(2026, 8, 21, 22, tzinfo=timezone.utc),
    )

    assert report.migrated == 2
    assert store.rows["ave-generated-id"]["metadata"]["capability"]["status"] == "active"


def test_explicit_mapping_tolerates_surrounding_whitespace_in_stored_person_id() -> None:
    store = MemoryPlayers([player(" player_7e49d6d016269f93 ", "Mai-Brit")])

    report = migrate_legacy_capabilities(
        store,
        {"mai_brit": {"capability": "mai-private-capability"}},
        mapping={"mai_brit": "player_7e49d6d016269f93"},
        clock=lambda: datetime(2026, 8, 21, 22, tzinfo=timezone.utc),
    )

    assert report.lines == ("mai_brit     MIGRATED",)


def test_identity_without_legacy_capability_is_safely_skipped() -> None:
    store = MemoryPlayers([player("ave-id", "Ave"), player("katia-id", "Katia")])

    report = migrate_legacy_capabilities(
        store,
        {
            "ave": {"capability": "ave-private-capability"},
            "katia": {"drop_token": "separate-drop-token"},
        },
        mapping={"ave": "ave-id", "katia": "katia-id"},
        clock=lambda: datetime(2026, 8, 21, 22, tzinfo=timezone.utc),
    )

    assert report.lines == (
        "ave          MIGRATED",
        "katia        SKIPPED · NO LEGACY CAPABILITY",
    )
    assert report.migrated == 1
    assert report.skipped == 1
    assert report.total == 2
