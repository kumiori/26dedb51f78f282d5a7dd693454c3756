import re
import tomllib

import pytest

from takeover.invite_secrets import batch_toml, generate_invite, invite_toml, participant_id


def test_generated_invite_has_drop_token_and_profile_capability() -> None:
    identity, values = generate_invite("Mai Brit!")
    assert identity == "mai_brit"
    assert set(values) == {"drop_token", "capability"}
    assert re.fullmatch(r"mai_brit-[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{4}", values["drop_token"])
    assert re.fullmatch(r"[A-Za-z0-9_-]{32,}", values["capability"])


def test_invite_toml_contains_both_credentials() -> None:
    identity, values = generate_invite("Ave")
    payload = tomllib.loads(invite_toml(identity, values))
    assert payload["takeover_identities"]["ave"] == values


def test_participant_id_rejects_empty_names() -> None:
    with pytest.raises(ValueError):
        participant_id(" !!! ")


def test_batch_toml_combines_multiple_invites() -> None:
    rows = [
        ("ave", {"drop_token": "ave-ABC2", "capability": "capability-for-ave"}),
        ("mai_brit", {"drop_token": "mai_brit-DEF5", "capability": "capability-for-mai"}),
    ]
    payload = tomllib.loads(batch_toml(rows))
    assert payload["takeover_identities"]["ave"]["drop_token"] == "ave-ABC2"
    assert payload["takeover_identities"]["ave"]["capability"] == "capability-for-ave"
    assert payload["takeover_identities"]["mai_brit"]["drop_token"] == "mai_brit-DEF5"
