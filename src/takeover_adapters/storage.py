"""Normalization of provider metadata at the adapter boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from takeover_engine import StorageObject


def storage_object_from_s3(row: Mapping[str, object], *, provider: str = "s3-compatible") -> StorageObject:
    modified = row.get("LastModified")
    if isinstance(modified, str):
        modified = datetime.fromisoformat(modified.replace("Z", "+00:00"))
    if not isinstance(modified, datetime):
        raise ValueError("S3 object requires LastModified")
    if modified.tzinfo is None:
        modified = modified.replace(tzinfo=timezone.utc)
    return StorageObject(
        key=str(row.get("Key") or ""), size_bytes=int(row.get("Size") or 0), modified_at=modified,
        etag=str(row.get("ETag") or "").strip('"'), provider=provider,
    )
