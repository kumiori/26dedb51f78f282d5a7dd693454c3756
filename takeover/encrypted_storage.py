"""Local metadata registry for client-encrypted Filebase objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EncryptedContribution:
    id: str
    contributor_id: str
    created_at: str
    object: dict[str, Any]
    crypto: dict[str, Any]
    visibility: str = "private"


class EncryptedRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> list[EncryptedContribution]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [EncryptedContribution(**row) for row in payload.get("contributions", [])]

    def add(self, row: EncryptedContribution) -> EncryptedContribution:
        rows = self.list()
        if any(existing.id == row.id or existing.object["key"] == row.object["key"] for existing in rows):
            return next(existing for existing in rows if existing.id == row.id or existing.object["key"] == row.object["key"])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"schema": "takeover-encrypted-storage/v1", "contributions": [asdict(item) for item in (*rows, row)]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)
        return row
