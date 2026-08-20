"""Validated schemas for encrypted contributions and stored ciphertext."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..domain import Visibility


def _required(value: str, name: str) -> str:
    clean = str(value).strip()
    if not clean:
        raise ValueError(f"{name} is required")
    return clean


@dataclass(frozen=True, slots=True)
class StorageObject:
    key: str
    size_bytes: int
    modified_at: datetime
    etag: str = ""
    provider: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _required(self.key, "storage key"))
        if self.size_bytes < 0:
            raise ValueError("storage size cannot be negative")
        if self.modified_at.tzinfo is None:
            raise ValueError("storage timestamp must be timezone-aware")
        object.__setattr__(self, "modified_at", self.modified_at.astimezone(timezone.utc))


@dataclass(frozen=True, slots=True)
class CryptoEnvelope:
    version: int
    algorithm: str
    iv: str
    kdf: str
    salt: str
    wrap_iv: str
    wrapped_key: str
    key_reference: str

    def __post_init__(self) -> None:
        if self.version != 1:
            raise ValueError("unsupported crypto envelope version")
        if self.algorithm != "AES-256-GCM" or self.kdf != "HKDF-SHA-256":
            raise ValueError("unsupported crypto envelope algorithms")
        for name in ("iv", "salt", "wrap_iv", "wrapped_key", "key_reference"):
            object.__setattr__(self, name, _required(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class Contribution:
    id: str
    contributor_id: str
    created_at: datetime
    object: StorageObject
    crypto: CryptoEnvelope
    visibility: Visibility | str = Visibility.PRIVATE

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required(self.id, "contribution id"))
        object.__setattr__(self, "contributor_id", _required(self.contributor_id, "contributor id"))
        if self.created_at.tzinfo is None:
            raise ValueError("contribution timestamp must be timezone-aware")
        object.__setattr__(self, "created_at", self.created_at.astimezone(timezone.utc))
        object.__setattr__(self, "visibility", Visibility(self.visibility))
