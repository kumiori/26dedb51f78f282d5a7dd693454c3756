"""Invitation routing values for database-backed player population."""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlencode


CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_LENGTH = 5


@dataclass(frozen=True)
class PlayerResolution:
    status: str
    person_id: str | None = None
    player: dict[str, Any] | None = None
    matches: int = 0

@dataclass(frozen=True)
class PlayerInvitationResult:
    player: dict[str, Any]
    relations: tuple[Any, ...]
    relation_readbacks: tuple[dict[str, Any], ...]
    code: str
    capability: str
    url: str
    message: str


class InvitationAlreadyExists(ValueError):
    pass


def create_invitation_credentials() -> tuple[str, str, str]:
    """Return a recognisable code, raw capability, and stored verifier."""
    code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
    capability = secrets.token_urlsafe(24)
    return code, capability, capability_verifier(capability)


def capability_verifier(capability: str) -> str:
    return hashlib.sha256(capability.encode("utf-8")).hexdigest()


def resolve_capability(
    store: Any,
    raw_capability: str,
    *,
    registry_status: str,
) -> PlayerResolution:
    """Resolve capability ownership through the authoritative player registry only."""
    if registry_status == "unavailable":
        return PlayerResolution("registry_unavailable")
    if registry_status == "degraded":
        return PlayerResolution("registry_degraded")
    candidate = raw_capability.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", candidate):
        return PlayerResolution("malformed")
    try:
        matches = store.find_players_by_capability_verifier(
            capability_verifier(candidate)
        )
    except Exception:
        return PlayerResolution("registry_degraded")
    if not matches:
        return PlayerResolution("unknown")
    if len(matches) != 1:
        return PlayerResolution("integrity_error", matches=len(matches))
    player = matches[0]
    capability = (player.get("metadata") or {}).get("capability") or {}
    if str(capability.get("status") or "") == "revoked":
        return PlayerResolution(
            "revoked", person_id=str(player["player_id"]), player=player, matches=1
        )
    if str(capability.get("status") or "") != "active":
        return PlayerResolution("unknown")
    return PlayerResolution(
        "resolved", person_id=str(player["player_id"]), player=player, matches=1
    )


def invitation_url(base_url: str, *, capability: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base.startswith(("https://", "http://")):
        raise ValueError("Website URL must begin with http:// or https://.")
    query = urlencode({"c": capability})
    return f"{base}/?{query}"


def invitation_message(name: str, code: str, url: str) -> str:
    return (
        f"TAKE OVER / INVITATION\n\n{name.strip()} · {code.strip().upper()}\n\n"
        "You have been invited to inhabit a node in TAKE OVER. Open this private link "
        "and add the few details that describe what you bring:\n\n"
        f"{url}\n\n"
        "After registration, the interface will explain the next step for uploading material."
    )


def _relation_id(source: str, relation_type: str, target: str) -> str:
    raw = f"relation-{source}-{relation_type}-{target}".lower()
    return re.sub(r"[^a-z0-9_-]+", "-", raw).strip("-")


def create_player_invitation(
    store: Any,
    *,
    name: str,
    inviter_id: str,
    practice: str,
    website_url: str,
    request_id: str,
    clock: Any,
    already_collaborating: bool = False,
    credential_factory: Any = create_invitation_credentials,
    label: str = "Person • Alien",
    project_stage: str = "application",
    node_stage: str = "invited",
    status: str = "draft",
    network_state: str = "latent_private",
    visibility: str = "public",
) -> PlayerInvitationResult:
    """Create one player and its factual invitation relation exactly once per request."""
    from .models import Relation
    from .node_population import PlayerPopulation, make_person_id, upsert_player_verified

    clean_request = request_id.strip()
    if not clean_request:
        raise ValueError("Invitation request ID is required.")
    if any(
        str((row.get("metadata") or {}).get("invitation_request_id") or "") == clean_request
        for row in store.list_players()
    ):
        raise InvitationAlreadyExists(f"Invitation request already exists: {clean_request}")
    issued_at = clock()
    if not isinstance(issued_at, datetime) or issued_at.tzinfo is None or issued_at.utcoffset() is None:
        raise ValueError("Invitation clock must return a timezone-aware datetime.")
    player_id, initial_condition = make_person_id(
        name, issued_at.isoformat(timespec="seconds")
    )
    code, capability, verifier = credential_factory()
    metadata = {
        "invitation_code": code,
        "capability": {
            "version": 1,
            "algorithm": "sha256",
            "verifier": verifier,
            "status": "active",
            "issued_at": issued_at.isoformat(),
            "revoked_at": None,
        },
        "invitation_request_id": clean_request,
        "invited_by": inviter_id,
    }
    player = upsert_player_verified(store, PlayerPopulation(
        player_id=player_id,
        name=name.strip(),
        label=label.strip() or "Person • Alien",
        practice=practice.strip(),
        metadata=metadata,
        initial_condition=initial_condition,
        project_stage=project_stage,
        node_stage=node_stage,
        status=status,
        network_state=network_state,
        visibility=visibility,
    ))
    provenance = {
        "provenance": "invitation_factory",
        "invitation_request_id": clean_request,
        "current_state": "active",
    }
    relations = [Relation(
        _relation_id(inviter_id, "invited", player_id),
        inviter_id,
        player_id,
        "invited",
        project_stage,
        "active",
        provenance,
    )]
    if already_collaborating:
        relations.append(Relation(
            _relation_id(inviter_id, "collaborates_with", player_id),
            inviter_id,
            player_id,
            "collaborates_with",
            project_stage,
            "active",
            {**provenance, "asserted_at_invitation": True},
        ))
    readbacks = tuple(store.upsert_player_relation(relation) for relation in relations)
    url = invitation_url(website_url, capability=capability)
    return PlayerInvitationResult(
        player=player,
        relations=tuple(relations),
        relation_readbacks=readbacks,
        code=code,
        capability=capability,
        url=url,
        message=invitation_message(name, code, url),
    )
