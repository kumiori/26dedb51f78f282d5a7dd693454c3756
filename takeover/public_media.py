"""Durable public media uploads for player-facing node material."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class PublicMediaUpload:
    url: str
    cid: str
    object_key: str
    bytes: int
    content_type: str


class FilebasePublicMediaStore:
    def __init__(self, client: Any, bucket: str, gateway: str) -> None:
        self.client = client
        self.bucket = bucket.strip()
        self.gateway = gateway.strip().rstrip("/")
        if not self.bucket or not self.gateway.startswith("https://"):
            raise ValueError("Public media bucket and HTTPS gateway are required.")

    def save_avatar(
        self,
        *,
        player_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> PublicMediaUpload:
        if not content_type.startswith("image/") or not data:
            raise ValueError("Avatar must be a non-empty image.")
        if len(data) > 10 * 1024 * 1024:
            raise ValueError("Avatar must be 10 MB or smaller.")
        safe_player = re.sub(r"[^A-Za-z0-9_-]+", "-", player_id).strip("-")
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip("-.") or "avatar"
        digest = hashlib.sha256(data).hexdigest()
        object_key = f"public/avatars/{safe_player}/{digest[:16]}-{safe_name}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )
        metadata = self.client.head_object(Bucket=self.bucket, Key=object_key)
        cid = str(
            (metadata.get("Metadata") or {}).get("cid")
            or (metadata.get("ResponseMetadata") or {}).get("HTTPHeaders", {}).get("x-amz-meta-cid")
            or ""
        ).strip()
        if not cid:
            raise ValueError("Filebase upload completed without a CID.")
        return PublicMediaUpload(
            url=f"{self.gateway}/{cid}",
            cid=cid,
            object_key=object_key,
            bytes=len(data),
            content_type=content_type,
        )
