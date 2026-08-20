"""Generate and safely append participant invitation secrets."""

from __future__ import annotations

import json
from pathlib import Path
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
    """Generate one short opaque token for participant link routing."""
    identity = participant_id(name)
    suffix = "".join(secrets.choice(DROP_TOKEN_ALPHABET) for _ in range(DROP_TOKEN_LENGTH))
    return identity, {
        "drop_token": f"{identity}-{suffix}",
    }


def invite_toml(identity: str, values: dict[str, str]) -> str:
    """Render one participant table accepted by Streamlit secrets."""
    identity = participant_id(identity)
    required = ("drop_token",)
    if any(not str(values.get(key, "")).strip() for key in required):
        raise ValueError("Invite values are incomplete.")
    lines = [f"[takeover_identities.{json.dumps(identity)}]"]
    lines.extend(f"{key} = {json.dumps(str(values[key]))}" for key in required)
    return "\n".join(lines) + "\n"


def batch_toml(invites: list[tuple[str, dict[str, str]]]) -> str:
    """Render several participant tables as one copyable TOML document."""
    return "\n".join(invite_toml(identity, values).rstrip() for identity, values in invites) + ("\n" if invites else "")


def append_invite(path: Path, identity: str, values: dict[str, str]) -> None:
    """Append without overwriting the file or an existing participant."""
    snippet = invite_toml(identity, values)
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    section = f"[takeover_identities.{json.dumps(participant_id(identity))}]"
    if section in current:
        raise ValueError(f"Participant already exists: {participant_id(identity)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    separator = "" if not current or current.endswith("\n\n") else ("\n" if current.endswith("\n") else "\n\n")
    path.write_text(current + separator + snippet, encoding="utf-8")
