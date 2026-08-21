import re
from datetime import datetime, timezone

import pytest

from takeover.player_invitations import (
    InvitationAlreadyExists,
    capability_verifier,
    create_player_invitation,
    create_invitation_credentials,
    invitation_message,
    invitation_url,
)


def test_invitation_has_short_recognition_code_and_strong_capability() -> None:
    code, capability, verifier = create_invitation_credentials()

    assert re.fullmatch(r"[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{5}", code)
    assert len(capability) >= 32
    assert verifier == capability_verifier(capability)
    assert capability not in verifier


def test_invitation_link_and_message_carry_name_code_and_capability() -> None:
    url = invitation_url(
        "https://takeover.example/", capability="private/value"
    )
    message = invitation_message("Mai Brit", "ABC23", url)

    assert url == "https://takeover.example/?c=private%2Fvalue"
    assert "Mai Brit · ABC23" in message
    assert "After registration" in message


def test_canonical_invitation_factory_is_idempotent_and_writes_directed_provenance() -> None:
    class Store:
        def __init__(self):
            self.players = []
            self.relations = []

        def list_players(self):
            return list(self.players)

        def upsert_player(self, payload):
            row = {
                "player_id": payload.player_id,
                "name": payload.name,
                "image_url": payload.image_url,
                "bio": payload.bio,
                "practice": payload.practice,
                "sample_url": payload.sample_url,
                "metadata": {**payload.metadata, "node_stage": payload.node_stage},
                "project_stage": payload.project_stage,
                "status": payload.status,
                "network_state": payload.network_state,
                "visibility": payload.visibility,
                "row_count": 1,
            }
            self.players.append(row)
            return row

        def upsert_player_relation(self, relation):
            self.relations.append(relation)
            return {"relation_id": relation.id, "metadata": relation.metadata}

    store = Store()
    result = create_player_invitation(
        store,
        name="Sasha",
        inviter_id="ave",
        practice="movement",
        website_url="https://takeover.example",
        request_id="request-123",
        clock=lambda: datetime(2026, 8, 21, 20, tzinfo=timezone.utc),
        credential_factory=lambda: ("AB23C", "private-capability", capability_verifier("private-capability")),
    )

    assert result.player["status"] == "draft"
    assert result.player["metadata"]["node_stage"] == "invited"
    assert result.relations[0].source == "ave"
    assert result.relations[0].target == result.player["player_id"]
    assert result.relations[0].type == "invited"
    assert result.relations[0].metadata == {
        "provenance": "invitation_factory",
        "invitation_request_id": "request-123",
        "current_state": "active",
    }
    assert result.url == "https://takeover.example/?c=private-capability"

    with pytest.raises(InvitationAlreadyExists):
        create_player_invitation(
            store,
            name="Sasha",
            inviter_id="ave",
            practice="movement",
            website_url="https://takeover.example",
            request_id="request-123",
            clock=lambda: datetime(2026, 8, 21, 20, tzinfo=timezone.utc),
        )
    assert len(store.players) == 1
    assert len(store.relations) == 1
