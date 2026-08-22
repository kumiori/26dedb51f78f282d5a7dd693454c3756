import re
from datetime import datetime, timezone

import pytest

from takeover.player_invitations import (
    InvitationRecord,
    InvitationAlreadyExists,
    capability_verifier,
    create_player_invitation,
    create_invitation_credentials,
    create_open_invitation,
    invite_entry_url,
    invitation_message,
    invitation_url,
    resolve_invitation,
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


def test_open_invitation_creates_no_player_and_uses_i_route() -> None:
    class Store:
        def __init__(self):
            self.invitations = []
            self.players = []

        def create_invitation(self, invitation):
            self.invitations.append(invitation)
            return invitation

        def find_invitations_by_code(self, code):
            return [item for item in self.invitations if item.code == code]

    store = Store()
    result = create_open_invitation(
        store,
        invited_by="kumiori", inviter_name="kumiori",
        website_url="https://takeover.example", note="come through",
        entry_hint="sound",
        clock=lambda: datetime(2026, 8, 22, 12, tzinfo=timezone.utc),
        code_factory=lambda: "K7M4",
    )

    assert result.url == "https://takeover.example/?i=K7M4"
    assert result.invitation.status == "open"
    assert result.invitation.invited_by == "kumiori"
    assert not store.players
    assert resolve_invitation(store, "k7m4", registry_status="available").status == "resolved"


def test_single_use_invitation_resolves_consumed_without_granting_capability() -> None:
    consumed = InvitationRecord(
        "K7M4", "kumiori", datetime(2026, 8, 22, tzinfo=timezone.utc),
        status="consumed", consumed_by="player_new",
    )
    store = type("Store", (), {
        "find_invitations_by_code": lambda self, code: [consumed],
    })()

    resolution = resolve_invitation(store, "K7M4", registry_status="available")
    assert resolution.status == "consumed"
    assert resolution.invitation.consumed_by == "player_new"
    assert invite_entry_url("https://takeover.example", code="K7M4").endswith("?i=K7M4")


def test_invitation_resolution_preserves_safe_source_access_diagnosis() -> None:
    class SourceNotFound(Exception):
        status = 404
        code = "object_not_found"

    class Store:
        def find_invitations_by_code(self, _code):
            raise SourceNotFound("secret provider response must not be exposed")

    resolution = resolve_invitation(Store(), "K7M4", registry_status="available")

    assert resolution.status == "registry_degraded"
    assert resolution.http_status == "404"
    assert resolution.provider_code == "object_not_found"
    assert resolution.diagnosis == (
        "INTERACTIONS SOURCE NOT SHARED OR MANIFEST MISMATCH"
    )
    assert "secret" not in str(resolution)


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
    assert result.player["metadata"]["capability"] == {
        "version": 1,
        "algorithm": "sha256",
        "verifier": capability_verifier("private-capability"),
        "status": "active",
        "issued_at": "2026-08-21T20:00:00+00:00",
        "revoked_at": None,
    }
    assert "private-capability" not in str(result.player)
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
