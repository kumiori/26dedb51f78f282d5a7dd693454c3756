"""Provisional START HERE records with person, contribution and event separation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, MutableMapping


PARTICIPANTS_KEY = "takeover_onboarding_participants"
CONTRIBUTIONS_KEY = "takeover_onboarding_contributions"
EVENTS_KEY = "takeover_onboarding_events"

ENTRY_MODES = (
    ("commission", "Commission / selection"),
    ("performance", "Performance / dance"),
    ("music", "Musician / live sound"),
    ("dj", "DJ"),
    ("visual", "Visual / wall artist"),
    ("technical", "Technical / production"),
    ("other", "Other / not sure yet"),
)


def persist_entry(
    state: MutableMapping[str, Any], *, participant_id: str, display_name: str,
    mode: str, contribution: dict[str, Any], occurred_at: datetime,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Upsert one provisional participant and append a distinct act and event."""
    if mode not in {item[0] for item in ENTRY_MODES}:
        raise ValueError("Unsupported entry mode.")
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("Entry time must be timezone-aware.")
    clean_id = participant_id.strip()
    if not clean_id:
        raise ValueError("Participant id is required.")
    timestamp = occurred_at.isoformat()
    participants = state.setdefault(PARTICIPANTS_KEY, {})
    contributions = state.setdefault(CONTRIBUTIONS_KEY, [])
    events = state.setdefault(EVENTS_KEY, [])
    current = participants.get(clean_id, {})
    participant = {
        **current,
        "id": clean_id,
        "display_name": display_name.strip(),
        "role": mode,
        "status": "active",
        "source": "invite",
        "authority": "provisional",
        "created_at": current.get("created_at", timestamp),
        "updated_at": timestamp,
    }
    participants[clean_id] = participant
    contribution_row = {
        "id": f"entry-{len(contributions) + 1}",
        "participant_id": clean_id,
        "mode": mode,
        "payload": deepcopy(contribution),
        "authority": "provisional",
        "created_at": timestamp,
    }
    contributions.append(contribution_row)
    event = {
        "id": f"entry-event-{len(events) + 1}",
        "type": "minimal_contribution_added",
        "actor": clean_id,
        "payload": {"contribution_id": contribution_row["id"], "mode": mode},
        "authority": "provisional",
        "occurred_at": timestamp,
    }
    events.append(event)
    return deepcopy(participant), deepcopy(contribution_row), deepcopy(event)
