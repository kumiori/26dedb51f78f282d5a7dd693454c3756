from pathlib import Path

import pytest

from takeover.node_population import PlayerPopulation, load_population_registry, make_person_id, person_id_from_initial_condition, resolve_population_participant


ROOT = Path(__file__).resolve().parents[1]


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
