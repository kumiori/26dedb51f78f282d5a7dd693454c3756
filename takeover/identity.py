"""TAKE OVER's 128-bit access keys and their reusable emoji projection."""

from __future__ import annotations

import math
import re
import secrets
from typing import Mapping


EMOJI_ALPHABET = [
    "🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "⭐", "🌟", "✨", "⚡", "🔥",
    "💧", "🌊", "🌬️", "🌀", "🌈", "❄️", "☄️", "🌋", "💎", "🧊", "🪐", "🌌", "🎇",
    "🎆", "🎈", "🎉", "🎯", "🎲", "🧠", "🫧", "🧬", "🔮", "🪄", "🛰️", "🚀", "🛸",
    "🛠️", "⚙️", "📡", "🔑", "🗝️", "📀", "💾", "🧲", "🪙", "🥇", "🎖️", "🔰",
    "♾️", "🪬", "🔺", "🔻", "🔷", "🔶", "⬛", "⬜", "🟥", "🟩", "🟦", "🟨",
]
EMOJI_SYMBOLS_PER_KEY = math.ceil(128 / math.log2(len(EMOJI_ALPHABET)))
EMOJI_PATTERN = re.compile(
    "|".join(sorted((re.escape(symbol) for symbol in EMOJI_ALPHABET), key=len, reverse=True))
)


def split_emoji_symbols(raw: str) -> list[str]:
    symbols: list[str] = []
    index = 0
    while index < len(raw):
        match = EMOJI_PATTERN.match(raw, index)
        if not match:
            return []
        symbols.append(match.group(0))
        index = match.end()
    return symbols


def hex_to_emoji(access_key: str) -> str:
    value = int(access_key, 16)
    symbols: list[str] = []
    base = len(EMOJI_ALPHABET)
    while value:
        value, remainder = divmod(value, base)
        symbols.append(EMOJI_ALPHABET[remainder])
    symbols.extend([EMOJI_ALPHABET[0]] * (EMOJI_SYMBOLS_PER_KEY - len(symbols)))
    return "".join(reversed(symbols))


def emoji_suffix(access_key: str, length: int = 4) -> str:
    return "".join(split_emoji_symbols(hex_to_emoji(access_key))[-length:])


def is_full_access_key(raw: str) -> bool:
    candidate = raw.strip()
    compact = candidate.replace(" ", "").replace("-", "")
    return bool(re.fullmatch(r"[0-9A-Fa-f]{32}", compact)) or len(split_emoji_symbols(candidate)) == EMOJI_SYMBOLS_PER_KEY


def resolve_identity(raw: str, identities: Mapping[str, Mapping[str, str]]) -> str | None:
    """Resolve a full canonical key or a unique emoji suffix of at least four symbols."""
    candidate = raw.strip()
    compact = candidate.replace(" ", "").replace("-", "").upper()
    if re.fullmatch(r"[0-9A-F]{32}", compact):
        matches = [name for name, cfg in identities.items() if secrets.compare_digest(cfg["access_key"].upper(), compact)]
        return matches[0] if len(matches) == 1 else None
    symbols = split_emoji_symbols(candidate)
    if len(symbols) < 4:
        return None
    matches = [
        name for name, cfg in identities.items()
        if split_emoji_symbols(hex_to_emoji(cfg["access_key"].upper()))[-len(symbols):] == symbols
    ]
    return matches[0] if len(matches) == 1 else None


def invitation_identity(raw_activation: str, capability: str, identities: Mapping[str, Mapping[str, str]]) -> str | None:
    participant = raw_activation.removeprefix("invite_")
    if raw_activation == participant or participant not in identities:
        return None
    expected = str(identities[participant].get("capability", ""))
    return participant if expected and secrets.compare_digest(expected, capability) else None


def resolve_drop_token(raw: str, identities: Mapping[str, Mapping[str, str]]) -> str | None:
    """Resolve one participant-scoped drop parameter to one participant."""
    candidate = raw.strip()
    matches = [
        participant for participant, cfg in identities.items()
        if str(cfg.get("drop_token", "")) and secrets.compare_digest(str(cfg["drop_token"]), candidate)
    ]
    return matches[0] if len(matches) == 1 else None
