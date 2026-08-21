"""Public provisional records for stage-driven inhabited nodes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, MutableMapping
import uuid

from .models import Entity


NODES_KEY = "takeover_inhabited_nodes"
NODE_STAGES = (
    "seeded", "node_population", "ready", "invited", "entering",
    "contributing", "active", "latent",
)


def node_stage(entity: Entity) -> str:
    stage = str(entity.metadata.get("node_stage") or "active")
    if stage not in NODE_STAGES:
        raise ValueError(f"Unsupported node stage: {stage}")
    return stage


def _build_node_record(
    *, node_id: str, avatar: dict[str, Any], text: str, practice: list[str],
    sample: dict[str, Any], clock: Callable[[], datetime],
) -> dict[str, Any]:
    clean_id = node_id.strip()
    if not clean_id:
        raise ValueError("Node id is required.")
    now = clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Node clock must return a timezone-aware datetime.")
    clean_practice = list(dict.fromkeys(item.strip() for item in practice if item.strip()))
    clean_avatar = deepcopy(avatar)
    clean_sample = deepcopy(sample)
    complete = bool((clean_avatar.get("url") or clean_avatar.get("cid") or clean_avatar.get("path")) and text.strip() and clean_practice)
    return {
        "node_id": clean_id,
        "stage": "ready" if complete else "node_population",
        "node": {
            "avatar": clean_avatar,
            "text": {"format": "markdown", "text": text.strip()},
            "practice": clean_practice,
            "sample": clean_sample,
        },
        "state": {
            "inhabited": True, "complete": complete, "authority": "provisional",
        },
        "updated_at": now.isoformat(),
    }


class NodeStore:
    """Session-local inhabited-node adapter; never presented as durable authority."""

    def __init__(self, state: MutableMapping[str, Any]) -> None:
        self.state = state
        state.setdefault(NODES_KEY, {})

    def get(self, node_id: str) -> dict[str, Any] | None:
        row = self.state[NODES_KEY].get(node_id)
        return deepcopy(row) if row else None

    def list_nodes(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self.state[NODES_KEY])

    def save(
        self, *, node_id: str, avatar: dict[str, Any], text: str,
        practice: list[str], sample: dict[str, Any], clock: Callable[[], datetime],
    ) -> dict[str, Any]:
        node = _build_node_record(node_id=node_id, avatar=avatar, text=text, practice=practice, sample=sample, clock=clock)
        self.state[NODES_KEY][node["node_id"]] = deepcopy(node)
        return deepcopy(node)


class FileNodeStore:
    """Shared local inhabited-node registry with first-completion locking."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text())
        if payload.get("schema_version") != "takeover-inhabited-nodes/v1":
            raise ValueError("Expected a takeover-inhabited-nodes/v1 document.")
        return dict(payload.get("nodes") or {})

    def get(self, node_id: str) -> dict[str, Any] | None:
        row = self._read().get(node_id)
        return deepcopy(row) if row else None

    def list_nodes(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._read())

    def save(
        self, *, node_id: str, avatar: dict[str, Any], text: str,
        practice: list[str], sample: dict[str, Any], clock: Callable[[], datetime],
    ) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(self.path.suffix + ".lock")
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
        except FileExistsError as exc:
            raise ValueError("Node save is already in progress.") from exc
        try:
            rows = self._read()
            if bool((rows.get(node_id) or {}).get("state", {}).get("complete")):
                raise ValueError("This node is already ready.")
            node = _build_node_record(node_id=node_id, avatar=avatar, text=text, practice=practice, sample=sample, clock=clock)
            rows[node_id] = deepcopy(node)
            temporary = self.path.with_suffix(f".{uuid.uuid4().hex}.tmp")
            temporary.write_text(json.dumps({"schema_version": "takeover-inhabited-nodes/v1", "nodes": rows}, ensure_ascii=False, indent=2) + "\n")
            temporary.replace(self.path)
            return deepcopy(node)
        finally:
            lock.unlink(missing_ok=True)


class PublicNodeMediaStore:
    """Store untouched public node media originals outside the registry."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def save_original(self, *, node_id: str, filename: str, content_type: str, data: bytes) -> dict[str, Any]:
        if not content_type.startswith("image/") or not data:
            raise ValueError("Avatar must be a non-empty image.")
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip("-.") or "avatar"
        digest = hashlib.sha256(data).hexdigest()
        target = self.root / node_id / f"{digest[:16]}-{safe_name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        return {"path": str(target), "filename": filename, "mime_type": content_type, "sha256": digest}

    def save_sample(self, *, node_id: str, filename: str, content_type: str, data: bytes) -> dict[str, Any]:
        if not data:
            raise ValueError("Sample must not be empty.")
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip("-.") or "sample"
        digest = hashlib.sha256(data).hexdigest()
        target = self.root / node_id / "samples" / f"{digest[:16]}-{safe_name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        return {"path": str(target), "filename": filename, "mime_type": content_type, "sha256": digest}


def apply_inhabited_nodes(entities: list[Entity], nodes: dict[str, dict[str, Any]]) -> list[Entity]:
    output: list[Entity] = []
    for entity in entities:
        record = nodes.get(entity.id)
        if record is None:
            output.append(entity)
            continue
        metadata = {
            **entity.metadata,
            "node_stage": record["stage"],
            "avatar": deepcopy(record["node"]["avatar"]),
            "practice": deepcopy(record["node"]["practice"]),
            "node_complete": bool(record["state"]["complete"]),
        }
        output.append(replace(entity, metadata=metadata))
    return output
