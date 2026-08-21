from copy import deepcopy
import hashlib
from pathlib import Path

from takeover.node_population import PlayerPopulation, make_person_id
from takeover.notion import NotionRegistry
from takeover.player_invitations import create_player_invitation


ROOT = Path(__file__).resolve().parents[1]


class FakeDataSources:
    def __init__(self, pages: "FakePages") -> None:
        self.pages = pages

    def query(self, *, data_source_id, filter=None, page_size=100, **_kwargs):
        rows = [
            row for row in self.pages.rows.values()
            if row["parent"].get("data_source_id") == data_source_id
        ]
        if filter:
            expected = filter["rich_text"]["equals"]
            rows = [
                row for row in rows
                if row["properties"][filter["property"]]["rich_text"][0]["text"]["content"] == expected
            ]
        return {"results": deepcopy(rows[:page_size]), "has_more": False}


class FakePages:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def create(self, *, parent, properties):
        page_id = f"player-{len(self.rows) + 1}"
        self.rows[page_id] = {"id": page_id, "parent": deepcopy(parent), "properties": self._returned(properties)}
        return deepcopy(self.rows[page_id])

    def update(self, *, page_id, properties, archived=False):
        self.rows[page_id]["properties"].update(self._returned(properties))
        self.rows[page_id]["archived"] = archived
        return deepcopy(self.rows[page_id])

    def retrieve(self, *, page_id):
        return deepcopy(self.rows[page_id])

    @staticmethod
    def _returned(properties):
        output = deepcopy(properties)
        for prop in output.values():
            for kind in ("title", "rich_text"):
                for value in prop.get(kind) or []:
                    value["plain_text"] = value["text"]["content"]
        return output


class FakeNotionClient:
    def __init__(self) -> None:
        self.pages = FakePages()
        self.data_sources = FakeDataSources(self.pages)


def test_player_population_create_then_update_is_one_stable_person_id() -> None:
    client = FakeNotionClient()
    registry = NotionRegistry("test-token", ROOT / "config" / "takeover_notion.json", client=client)

    created = registry.upsert_player(PlayerPopulation(
        player_id="kumiori", name="kumiori", image_url="https://example.test/one.jpg",
        bio="First inhabitation", practice="systems, images", sample_url="https://example.test/one",
        metadata={"crop": {"x": 0.5, "y": 0.4}},
    ))
    updated = registry.upsert_player(PlayerPopulation(
        player_id="kumiori", name="kumiori", image_url="https://example.test/two.jpg",
        bio="Second inhabitation", practice="systems, images, sound", sample_url="https://example.test/two",
        metadata={"crop": {"x": 0.6, "y": 0.4}}, network_state="latent_known", visibility="public",
    ))

    assert len(client.pages.rows) == 1
    assert created["action"] == "CREATED"
    assert updated["action"] == "UPDATED"
    assert created["player_id"] == updated["player_id"] == "kumiori"
    assert updated["bio"] == "Second inhabitation"
    assert updated["practice"] == "systems, images, sound"
    assert updated["sample_url"] == "https://example.test/two"
    assert updated["metadata"] == {"crop": {"x": 0.6, "y": 0.4}, "node_stage": "node_population"}
    assert updated["project_stage"] == "application"
    assert updated["status"] == "active"
    assert updated["network_state"] == "latent_known"
    assert updated["visibility"] == "public"
    assert updated["row_count"] == 1
    assert updated["duplicates"] == 0
    assert registry.count_players("kumiori") == 1
    assert registry.read_player("kumiori")["bio"] == "Second inhabitation"
    assert registry.read_player("unknown") is None


def test_general_entity_loader_keeps_player_facing_fields() -> None:
    client = FakeNotionClient()
    registry = NotionRegistry("test-token", ROOT / "config" / "takeover_notion.json", client=client)
    registry.upsert_player(PlayerPopulation(
        player_id="kumiori", name="kumiori", image_url="https://example.test/avatar.jpg",
        bio="A short inhabitation", practice="theory, images",
        sample_url="https://example.test/sample", metadata={"crop": {"x": 0.4}},
    ))

    entity = registry._entities("players", "person", "Person ID")[0]

    assert entity.source == "https://example.test/avatar.jpg"
    assert entity.metadata == {
        "crop": {"x": 0.4},
        "node_stage": "node_population",
        "bio": "A short inhabitation",
        "practice": "theory, images",
        "sample_url": "https://example.test/sample",
        "avatar": {"url": "https://example.test/avatar.jpg"},
        "registry_status": "active",
        "visibility": "public",
    }


def test_private_player_entity_does_not_project_private_human_content() -> None:
    client = FakeNotionClient()
    registry = NotionRegistry("test-token", ROOT / "config" / "takeover_notion.json", client=client)
    registry.upsert_player(PlayerPopulation(
        player_id="private-id", name="Private Name", bio="secret", practice="secret practice",
        sample_url="https://secret.invalid", image_url="https://secret.invalid/avatar.jpg",
        network_state="latent_private", visibility="private",
    ))

    entity = registry._entities("players", "person", "Person ID")[0]

    assert entity.title == "PRIVATE"
    assert entity.status == "latent_private"
    assert entity.source == ""
    assert "bio" not in entity.metadata
    assert entity.metadata["visibility"] == "private"


def test_player_relation_upsert_uses_stable_id_and_real_player_endpoints() -> None:
    from takeover.models import Relation

    client = FakeNotionClient()
    registry = NotionRegistry("test-token", ROOT / "config" / "takeover_notion.json", client=client)
    registry.upsert_player(PlayerPopulation(player_id="kumiori", name="kumiori"))
    registry.upsert_player(PlayerPopulation(player_id="ave", name="Ave"))

    relation = Relation(
        "relation-kumiori-ave",
        "kumiori",
        "ave",
        "collaborates_with",
        metadata={"provenance": "test"},
    )
    created = registry.upsert_player_relation(relation)
    updated = registry.upsert_player_relation(relation)

    assert created["action"] == "CREATED"
    assert updated["action"] == "UPDATED"
    assert updated["relation_id"] == "relation-kumiori-ave"
    assert updated["source"] == "kumiori"
    assert updated["target"] == "ave"
    assert updated["metadata"] == {"provenance": "test"}
    assert registry.list_relations() == [relation]


def test_generated_player_initial_condition_survives_mutable_updates() -> None:
    client = FakeNotionClient()
    registry = NotionRegistry("test-token", ROOT / "config" / "takeover_notion.json", client=client)
    person_id, initial = make_person_id(
        "Ave", "2026-08-21T17:53:00+02:00", nonce="7c91f2a8",
    )
    registry.upsert_player(PlayerPopulation(
        player_id=person_id, name="Ave", bio="first", initial_condition=initial,
    ))
    updated = registry.upsert_player(PlayerPopulation(
        player_id=person_id, name="Ave Renamed", bio="second", practice="mutable",
        initial_condition=initial,
    ))

    assert len(client.pages.rows) == 1
    assert updated["name"] == "Ave Renamed"
    assert updated["bio"] == "second"
    assert updated["initial_condition"] == initial
    assert updated["metadata"]["initial_condition"] == initial


def test_invitation_resolves_only_with_code_and_matching_private_capability() -> None:
    client = FakeNotionClient()
    registry = NotionRegistry("test-token", ROOT / "config" / "takeover_notion.json", client=client)
    capability = "a-long-private-capability"
    registry.upsert_player(PlayerPopulation(
        player_id="invited-player",
        name="Invited Player",
        metadata={
            "invitation_code": "AB23C",
            "invitation_capability_hash": hashlib.sha256(capability.encode()).hexdigest(),
        },
        node_stage="invited",
        network_state="latent_private",
    ))

    resolved = registry.resolve_player_invitation("ab23c", capability)
    entity = registry._entities("players", "person", "Person ID")[0]

    assert resolved and resolved["player_id"] == "invited-player"
    assert "invitation_capability_hash" not in entity.metadata
    assert registry.resolve_unfinished_player_capability(capability)["player_id"] == "invited-player"
    assert registry.resolve_player_invitation("AB23C", "wrong") is None
    assert registry.resolve_player_invitation("WRONG", capability) is None

    registry.upsert_player(PlayerPopulation(
        player_id="invited-player",
        name="Invited Player",
        metadata={
            "invitation_code": "AB23C",
            "invitation_capability_hash": hashlib.sha256(capability.encode()).hexdigest(),
        },
        node_stage="ready",
        network_state="active",
    ))
    assert registry.resolve_unfinished_player_capability(capability) is None


def test_capability_resolution_is_unique_visible_and_survives_ready_transition() -> None:
    client = FakeNotionClient()
    registry = NotionRegistry("test-token", ROOT / "config" / "takeover_notion.json", client=client)
    capability = "one-player-scoped-capability"
    verifier = hashlib.sha256(capability.encode()).hexdigest()
    registry.upsert_player(PlayerPopulation(
        player_id="owner",
        name="Owner",
        metadata={"invitation_capability_hash": verifier},
        node_stage="node_population",
    ))

    first = registry.resolve_player_capability(capability)
    assert first.status == "resolved"
    assert first.player and first.player["player_id"] == "owner"
    assert first.player["metadata"]["node_stage"] == "node_population"

    registry.upsert_player(PlayerPopulation(
        player_id="owner",
        name="Owner",
        metadata={"invitation_capability_hash": verifier},
        node_stage="ready",
    ))
    reopened = registry.resolve_player_capability(capability)
    assert reopened.status == "resolved"
    assert reopened.player and reopened.player["metadata"]["node_stage"] == "ready"

    registry.upsert_player(PlayerPopulation(
        player_id="duplicate-owner",
        name="Duplicate",
        metadata={"invitation_capability_hash": verifier},
        node_stage="node_population",
    ))
    assert registry.resolve_player_capability(capability).status == "duplicate"
    assert registry.resolve_player_capability("invalid").status == "invalid"


def test_fresh_adapter_recovers_same_ready_player_and_saved_human_state() -> None:
    from datetime import datetime, timezone

    client = FakeNotionClient()
    first_registry = NotionRegistry(
        "test-token", ROOT / "config" / "takeover_notion.json", client=client
    )
    first_registry.upsert_player(PlayerPopulation(player_id="ave", name="Ave"))
    invite = create_player_invitation(
        first_registry,
        name="Sasha",
        inviter_id="ave",
        practice="movement",
        website_url="https://takeover.example",
        request_id="recovery-request",
        clock=lambda: datetime(2026, 8, 21, 20, tzinfo=timezone.utc),
    )
    entry = first_registry.resolve_player_capability(invite.capability)
    assert entry.status == "resolved" and entry.player
    row = entry.player
    first_registry.upsert_player(PlayerPopulation(
        player_id=row["player_id"],
        name=row["name"],
        label=row["label"],
        image_url="https://example.test/sasha.jpg",
        bio="Recovered text",
        practice="movement, listening",
        sample_url="https://example.test/sample",
        metadata=row["metadata"],
        initial_condition=row["initial_condition"],
        project_stage="application",
        node_stage="ready",
        status="active",
        network_state="active",
        visibility="public",
    ))

    reopened_registry = NotionRegistry(
        "test-token", ROOT / "config" / "takeover_notion.json", client=client
    )
    reopened = reopened_registry.resolve_player_capability(invite.capability)

    assert reopened.status == "resolved" and reopened.player
    assert reopened.player["player_id"] == row["player_id"]
    assert reopened.player["bio"] == "Recovered text"
    assert reopened.player["practice"] == "movement, listening"
    assert reopened.player["image_url"] == "https://example.test/sasha.jpg"
    assert reopened.player["sample_url"] == "https://example.test/sample"
    assert reopened.player["metadata"]["node_stage"] == "ready"
