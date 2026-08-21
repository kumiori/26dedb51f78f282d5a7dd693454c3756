"""Generate copyable participant invitation credentials."""

from __future__ import annotations

import json
import re
import secrets


DROP_TOKEN_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
DROP_TOKEN_LENGTH = 4


def participant_id(name: str) -> str:
    """Return a stable TOML-safe participant identifier."""
    value = re.sub(r"[^a-z0-9_-]+", "_", name.strip().lower()).strip("_-")
    if not value:
        raise ValueError("Enter a participant name.")
    return value[:64]


def generate_invite(name: str) -> tuple[str, dict[str, str]]:
    """Generate separate private-drop and profile-edit credentials."""
    identity = participant_id(name)
    suffix = "".join(secrets.choice(DROP_TOKEN_ALPHABET) for _ in range(DROP_TOKEN_LENGTH))
    return identity, {
        "drop_token": f"{identity}-{suffix}",
        "capability": secrets.token_urlsafe(24),
    }


def invite_toml(identity: str, values: dict[str, str]) -> str:
    """Render one participant table accepted by Streamlit secrets."""
    identity = participant_id(identity)
    required = ("drop_token", "capability")
    if any(not str(values.get(key, "")).strip() for key in required):
        raise ValueError("Invite values are incomplete.")
    lines = [f"[takeover_identities.{json.dumps(identity)}]"]
    lines.extend(f"{key} = {json.dumps(str(values[key]))}" for key in required)
    return "\n".join(lines) + "\n"


def batch_toml(invites: list[tuple[str, dict[str, str]]]) -> str:
    """Render several participant tables as one copyable TOML document."""
    return "\n".join(invite_toml(identity, values).rstrip() for identity, values in invites) + ("\n" if invites else "")
