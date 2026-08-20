"""Development-only JSON persistence for encrypted contribution metadata."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

from takeover_engine import Contribution, CryptoEnvelope, StorageObject


class DevelopmentJsonContributionRegistry:
    """Atomic local metadata store for tests and development, not production."""

    schema = "takeover-contributions/v1"

    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> tuple[Contribution, ...]:
        if not self.path.exists():
            return ()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema") != self.schema:
            raise ValueError("unsupported contribution registry schema")
        return tuple(self._decode(row) for row in payload.get("contributions", []))

    def add(self, contribution: Contribution) -> Contribution:
        rows = self.list()
        duplicate = next((row for row in rows if row.id == contribution.id or row.object.key == contribution.object.key), None)
        if duplicate:
            return duplicate
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps({"schema": self.schema, "contributions": [self._encode(row) for row in (*rows, contribution)]}, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
        return contribution

    @staticmethod
    def _encode(row: Contribution) -> dict[str, object]:
        data = asdict(row)
        data["created_at"] = row.created_at.isoformat()
        data["visibility"] = row.visibility.value
        data["object"]["modified_at"] = row.object.modified_at.isoformat()
        return data

    @staticmethod
    def _decode(row: dict[str, object]) -> Contribution:
        object_row = dict(row["object"])
        crypto_row = dict(row["crypto"])
        object_row["modified_at"] = datetime.fromisoformat(str(object_row["modified_at"]))
        return Contribution(
            id=str(row["id"]), contributor_id=str(row["contributor_id"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            object=StorageObject(**object_row), crypto=CryptoEnvelope(**crypto_row),
            visibility=str(row.get("visibility", "private")),
        )
