from pathlib import Path

import pytest

from takeover.models import Entity
from takeover.node_population import (
    PlayerPopulation,
    load_population_registry,
    make_person_id,
    person_id_from_initial_condition,
    population_state,
    resolve_population_participant,
    upsert_player_verified,
    upsert_inhabited_node,
)


ROOT = Path(__file__).resolve().parents[1]


def test_population_state_allows_partial_save_but_only_completes_all_four_fields() -> None:
    partial = population_state("", "bio", "practice", "sample")
    assert partial.can_save
    assert not partial.complete
    assert partial.node_stage == "node_population"
    assert partial.missing == ("avatar",)

    complete = population_state("avatar", "bio", "practice", "sample")
    assert complete.can_save
    assert complete.complete
    assert complete.node_stage == "ready"
    assert complete.missing == ()

    assert not population_state("", "", "", "").can_save


def test_activation_aliases_resolve_to_canonical_seeded_node_ids() -> None:
    registry = load_population_registry(ROOT / "config" / "takeover_node_population.yaml")
    assert resolve_population_participant(registry, "ave") == "ave"
    assert resolve_population_participant(registry, "maibrit") == "mai_brit"
    assert resolve_population_participant(registry, "Mai-Brit") == "mai_brit"
    assert resolve_population_participant(registry, "sophonisba") is None


def test_person_id_hashes_only_the_canonical_immutable_initial_condition() -> None:
    person_id, initial = make_person_id(
        "  Ave  ", "2026-08-21T17:53:00+02:00", nonce="7c91f2a8",
    )
    same_id, same_initial = make_person_id(
        "ave", "2026-08-21T17:53:00+02:00", nonce="7c91f2a8",
    )

    assert person_id == same_id == person_id_from_initial_condition(initial)
    assert person_id.startswith("player_") and len(person_id) == 23
    assert initial == same_initial == {
        "name": "ave", "t0": "2026-08-21T17:53:00+02:00",
        "origin": "takeover", "nonce": "7c91f2a8",
    }
    assert PlayerPopulation(player_id=person_id, name="AVE RENAMED", bio="mutable", initial_condition=initial)


def test_generated_person_id_requires_its_original_timezone_aware_condition() -> None:
    person_id, initial = make_person_id("ave", "2026-08-21T17:53:00+02:00", nonce="7c91f2a8")
    changed = {**initial, "name": "someone else"}
    with pytest.raises(ValueError, match="does not match"):
        PlayerPopulation(player_id=person_id, name="Ave", initial_condition=changed)
    with pytest.raises(ValueError, match="timezone"):
        make_person_id("ave", "2026-08-21T17:53:00", nonce="7c91f2a8")


def test_inhabit_node_uses_production_player_upsert_contract() -> None:
    class RecordingStore:
        def upsert_player(self, payload):
            self.payload = payload
            return {
                "action": "UPDATED",
                "player_id": payload.player_id,
                "image_url": payload.image_url,
                "bio": payload.bio,
                "practice": payload.practice,
                "sample_url": payload.sample_url,
                "project_stage": payload.project_stage,
                "status": payload.status,
                "metadata": {"node_stage": payload.node_stage},
                "row_count": 1,
            }

    store = RecordingStore()
    entity = Entity(
        "ave",
        "person",
        "Ave",
        "Person • Alien",
        metadata={
            "node_stage": "node_population",
            "registry_status": "active",
            "visibility": "public",
            "bio": "old projected value",
        },
    )

    result = upsert_inhabited_node(
        store,
        entity,
        image_url="https://example.test/avatar.jpg",
        bio="New note",
        practice="movement, sound",
        sample_url="https://example.test/sample",
        crop={"x": 0.4, "y": 0.6, "scale": 1.2},
    )

    assert result["action"] == "UPDATED"
    assert result["player_id"] == "ave"
    assert store.payload.bio == "New note"
    assert store.payload.practice == "movement, sound"
    assert store.payload.node_stage == "ready"
    assert store.payload.metadata["avatar_crop"] == {"x": 0.4, "y": 0.6, "scale": 1.2}
    assert "bio" not in store.payload.metadata


def test_verified_upsert_rejects_a_mismatched_readback() -> None:
    class MismatchingStore:
        def upsert_player(self, payload):
            return {
                "player_id": payload.player_id,
                "image_url": payload.image_url,
                "bio": "discarded",
                "practice": payload.practice,
                "sample_url": payload.sample_url,
                "project_stage": payload.project_stage,
                "status": payload.status,
                "metadata": {"node_stage": payload.node_stage},
                "row_count": 1,
            }

    payload = PlayerPopulation(player_id="ave", name="Ave", bio="submitted")
    with pytest.raises(ValueError, match="Bio"):
        upsert_player_verified(MismatchingStore(), payload)
