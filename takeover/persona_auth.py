"""Minimal persona authentication with explicit provisional persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import secrets
from typing import Callable, MutableMapping

from .identity import emoji_suffix, hex_to_emoji, resolve_identity


PERSONAS_KEY = "takeover_personas"
INTERACTIONS_KEY = "takeover_persona_interactions"


@dataclass(frozen=True)
class Persona:
    access_key: str
    nickname: str
    emoji: str
    emoji_suffix_4: str
    emoji_suffix_6: str
    authority: str
    created_at: str
    last_authenticated_at: str


@dataclass(frozen=True)
class AuthenticationInteraction:
    id: str
    kind: str
    persona_key: str
    occurred_at: str
    authority: str
    interface: str = "authentication-test"


@dataclass(frozen=True)
class AuthenticationResult:
    persona: Persona
    interaction: AuthenticationInteraction


class ProvisionalPersonaStore:
    """Session-local adapter. Its records are never described as authoritative."""

    def __init__(self, state: MutableMapping[str, object]) -> None:
        self.state = state
        self.state.setdefault(PERSONAS_KEY, {})
        self.state.setdefault(INTERACTIONS_KEY, [])

    def upsert_persona(self, persona: Persona) -> Persona:
        personas = self.state[PERSONAS_KEY]
        assert isinstance(personas, dict)
        current = personas.get(persona.access_key, {})
        personas[persona.access_key] = {**current, **asdict(persona)}
        return persona

    def get_persona(self, access_key: str) -> Persona | None:
        personas = self.state[PERSONAS_KEY]
        assert isinstance(personas, dict)
        row = personas.get(access_key)
        return Persona(**row) if row else None

    def list_personas(self) -> list[Persona]:
        personas = self.state[PERSONAS_KEY]
        assert isinstance(personas, dict)
        return [Persona(**row) for row in personas.values()]

    def append_interaction(self, interaction: AuthenticationInteraction) -> None:
        interactions = self.state[INTERACTIONS_KEY]
        assert isinstance(interactions, list)
        interactions.append(asdict(interaction))

    def list_interactions(self) -> list[AuthenticationInteraction]:
        interactions = self.state[INTERACTIONS_KEY]
        assert isinstance(interactions, list)
        return [AuthenticationInteraction(**row) for row in interactions]


def _iso(clock: Callable[[], datetime]) -> str:
    now = clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Authentication clock must return a timezone-aware datetime.")
    return now.isoformat()


def _interaction(kind: str, access_key: str, occurred_at: str) -> AuthenticationInteraction:
    return AuthenticationInteraction(
        id=secrets.token_hex(16),
        kind=kind,
        persona_key=access_key,
        occurred_at=occurred_at,
        authority="provisional",
    )


def mint_persona(
    store: ProvisionalPersonaStore,
    *,
    nickname: str,
    key_factory: Callable[[], str],
    clock: Callable[[], datetime],
) -> AuthenticationResult:
    access_key = key_factory().strip().upper()
    if len(access_key) != 32 or any(char not in "0123456789ABCDEF" for char in access_key):
        raise ValueError("Persona keys must be 128-bit hexadecimal values.")
    occurred_at = _iso(clock)
    persona = Persona(
        access_key=access_key,
        nickname=nickname.strip(),
        emoji=hex_to_emoji(access_key),
        emoji_suffix_4=emoji_suffix(access_key, 4),
        emoji_suffix_6=emoji_suffix(access_key, 6),
        authority="provisional",
        created_at=occurred_at,
        last_authenticated_at=occurred_at,
    )
    store.upsert_persona(persona)
    interaction = _interaction("persona_minted", access_key, occurred_at)
    store.append_interaction(interaction)
    return AuthenticationResult(persona, interaction)


def authenticate_persona(
    store: ProvisionalPersonaStore,
    raw_key: str,
    *,
    clock: Callable[[], datetime],
) -> AuthenticationResult | None:
    personas = store.list_personas()
    identities = {persona.access_key: {"access_key": persona.access_key} for persona in personas}
    access_key = resolve_identity(raw_key, identities)
    if access_key is None:
        return None
    current = store.get_persona(access_key)
    if current is None:
        return None
    occurred_at = _iso(clock)
    persona = Persona(**{**asdict(current), "last_authenticated_at": occurred_at})
    store.upsert_persona(persona)
    interaction = _interaction("persona_authenticated", access_key, occurred_at)
    store.append_interaction(interaction)
    return AuthenticationResult(persona, interaction)
