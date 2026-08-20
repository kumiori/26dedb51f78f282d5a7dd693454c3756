"""Independent reference consumer: no Fotografiska configuration or UI."""

from takeover_engine import Entity, Overlay, RegistryState, Relation, apply_overlay, project_network


def build_team_network():
    facts = RegistryState(entities=(Entity("host", "person", "Host"),), source="consumer")
    temporary = Overlay(
        "guest-preview",
        entities=(Entity("guest", "person", "Guest"),),
        relations=(Relation("welcome", "host", "guest", "welcomes"),),
    )
    return project_network(apply_overlay(facts, temporary).state)


if __name__ == "__main__":
    network = build_team_network()
    print(f"{len(network.nodes)} nodes / {len(network.edges)} edges")
