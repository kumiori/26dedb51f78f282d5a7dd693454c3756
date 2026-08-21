from pathlib import Path

from takeover.node_population import load_population_registry, resolve_population_participant


ROOT = Path(__file__).resolve().parents[1]


def test_activation_aliases_resolve_to_canonical_seeded_node_ids() -> None:
    registry = load_population_registry(ROOT / "config" / "takeover_node_population.yaml")
    assert resolve_population_participant(registry, "ave") == "ave"
    assert resolve_population_participant(registry, "maibrit") == "mai_brit"
    assert resolve_population_participant(registry, "Mai-Brit") == "mai_brit"
    assert resolve_population_participant(registry, "sophonisba") is None
