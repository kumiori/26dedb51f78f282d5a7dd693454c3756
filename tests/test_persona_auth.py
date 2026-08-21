from datetime import datetime, timezone

from takeover.persona_auth import ProvisionalPersonaStore, mint_persona, authenticate_persona


NOW = datetime(2026, 8, 21, 10, 30, tzinfo=timezone.utc)


def test_minting_upserts_one_persona_and_records_the_interaction() -> None:
    state: dict = {}
    store = ProvisionalPersonaStore(state)

    result = mint_persona(
        store,
        nickname="Visitor",
        key_factory=lambda: "DBF25C24B1FFDC3B6C3E5B074274A0A8",
        clock=lambda: NOW,
    )

    assert result.persona.access_key == "DBF25C24B1FFDC3B6C3E5B074274A0A8"
    assert result.persona.emoji_suffix_4 == "⬜🥇⭐📀"
    assert result.persona.authority == "provisional"
    assert result.interaction.kind == "persona_minted"
    assert len(store.list_personas()) == 1
    assert len(store.list_interactions()) == 1


def test_authentication_by_unique_emoji_suffix_does_not_duplicate_persona() -> None:
    state: dict = {}
    store = ProvisionalPersonaStore(state)
    minted = mint_persona(
        store,
        nickname="Visitor",
        key_factory=lambda: "DBF25C24B1FFDC3B6C3E5B074274A0A8",
        clock=lambda: NOW,
    )

    authenticated = authenticate_persona(
        store,
        minted.persona.emoji_suffix_4,
        clock=lambda: NOW,
    )

    assert authenticated is not None
    assert authenticated.persona.access_key == minted.persona.access_key
    assert authenticated.interaction.kind == "persona_authenticated"
    assert len(store.list_personas()) == 1
    assert len(store.list_interactions()) == 2
