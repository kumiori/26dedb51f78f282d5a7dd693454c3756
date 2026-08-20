import re
import tomllib

import pytest

from takeover.invite_secrets import append_invite, batch_toml, generate_invite, participant_id


def test_generated_invite_has_only_one_short_drop_token() -> None:
    identity, values = generate_invite("Mai Brit!")
    assert identity == "mai_brit"
    assert set(values) == {"drop_token"}
    assert re.fullmatch(r"mai_brit-[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{4}", values["drop_token"])


def test_append_invite_preserves_existing_secrets_and_refuses_duplicates(tmp_path) -> None:
    path = tmp_path / ".streamlit" / "secrets.toml"
    path.parent.mkdir()
    path.write_text('[filebase]\nbucket = "existing"\n', encoding="utf-8")
    identity, values = generate_invite("Ave")

    append_invite(path, identity, values)
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    assert payload["filebase"]["bucket"] == "existing"
    assert payload["takeover_identities"]["ave"] == values
    with pytest.raises(ValueError, match="already exists"):
        append_invite(path, identity, values)


def test_participant_id_rejects_empty_names() -> None:
    with pytest.raises(ValueError):
        participant_id(" !!! ")


def test_batch_toml_combines_multiple_invites() -> None:
    rows = [
        ("ave", {"drop_token": "ave-ABC2"}),
        ("mai_brit", {"drop_token": "mai_brit-DEF5"}),
    ]
    payload = tomllib.loads(batch_toml(rows))
    assert payload["takeover_identities"]["ave"]["drop_token"] == "ave-ABC2"
    assert payload["takeover_identities"]["mai_brit"]["drop_token"] == "mai_brit-DEF5"
