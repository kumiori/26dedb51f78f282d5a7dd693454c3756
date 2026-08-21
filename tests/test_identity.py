from takeover.identity import emoji_suffix, hex_to_emoji, invitation_identity, is_full_access_key, node_write_identity, resolve_drop_token, resolve_identity, split_emoji_symbols


IDENTITIES = {
    "ave": {"access_key": "ECB7AD5B28E3DED2C2C6B95CD9A00E5B", "capability": "invite-capability", "drop_token": "ave-TEST"},
    "kenneerik": {"access_key": "DBF25C24B1FFDC3B6C3E5B074274A0A8", "capability": "another-capability", "drop_token": "kenneerik-DEMO"},
}


def test_full_and_short_emoji_keys_resolve_identity() -> None:
    full = hex_to_emoji(IDENTITIES["kenneerik"]["access_key"])
    assert len(split_emoji_symbols(full)) == 22
    assert resolve_identity(full, IDENTITIES) == "kenneerik"
    assert resolve_identity(emoji_suffix(IDENTITIES["kenneerik"]["access_key"]), IDENTITIES) == "kenneerik"
    assert resolve_identity(IDENTITIES["kenneerik"]["access_key"], IDENTITIES) == "kenneerik"
    assert is_full_access_key(full)
    assert is_full_access_key(IDENTITIES["kenneerik"]["access_key"])
    assert not is_full_access_key(emoji_suffix(IDENTITIES["kenneerik"]["access_key"]))


def test_invitation_capability_selects_but_does_not_authenticate_identity() -> None:
    assert invitation_identity("invite_ave", "invite-capability", IDENTITIES) == "ave"
    assert invitation_identity("invite_ave", "wrong", IDENTITIES) is None
    assert invitation_identity("ave", "invite-capability", IDENTITIES) is None


def test_node_write_capability_is_scoped_to_one_participant() -> None:
    assert node_write_identity("ave", "invite-capability", IDENTITIES) == "ave"
    assert node_write_identity("ave", "wrong", IDENTITIES) is None
    assert node_write_identity("kenneerik", "invite-capability", IDENTITIES) is None


def test_single_participant_drop_token_resolves_participant() -> None:
    assert resolve_drop_token("kenneerik-DEMO", IDENTITIES) == "kenneerik"
    assert resolve_drop_token("DEMO", IDENTITIES) is None
    assert resolve_drop_token("kenneerik-WRONG", IDENTITIES) is None
