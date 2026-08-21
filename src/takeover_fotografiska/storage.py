"""Fotografiska-specific ciphertext object naming policy."""

from __future__ import annotations

import re


_SEGMENT = re.compile(r"^[A-Za-z0-9_-]+$")


def _segment(value: str, name: str) -> str:
    clean = str(value).strip()
    if not _SEGMENT.fullmatch(clean):
        raise ValueError(f"{name} must contain only letters, numbers, underscores, or dashes")
    return clean


def encrypted_object_prefix(participant_id: str, namespace: str) -> str:
    """Return the application-owned public bucket prefix for encrypted objects."""
    participant = _segment(participant_id, "participant id")
    scope = _segment(namespace, "storage namespace")
    return f"public/{participant}/{scope}/"


def encrypted_object_key(participant_id: str, namespace: str, contribution_id: str) -> str:
    """Return one public-path key whose payload remains encrypted ciphertext."""
    contribution = _segment(contribution_id, "contribution id")
    return f"{encrypted_object_prefix(participant_id, namespace)}{contribution}.enc"
