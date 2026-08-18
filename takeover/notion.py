"""Notion-backed registry for the Takeover database family."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from notion_client import Client

from .models import Entity, Necessity, Relation


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "takeover_notion.json"


def _plain(prop: dict[str, Any]) -> str:
    values = prop.get("title") or prop.get("rich_text") or []
    return "".join(str(value.get("plain_text") or "") for value in values)


def _select(prop: dict[str, Any]) -> str:
    return str((prop.get("select") or {}).get("name") or "")


def _relation_id(prop: dict[str, Any]) -> str:
    values = prop.get("relation") or []
    return str(values[0].get("id") or "") if values else ""


def _text(value: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": str(value)}}]


class NotionRegistry:
    def __init__(self, token: str, manifest_path: Path = DEFAULT_MANIFEST) -> None:
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.sources = {
            key: value["data_source_id"]
            for key, value in self.manifest["databases"].items()
        }
        self.stage_pages = dict(self.manifest["stage_pages"])
        self.stage_by_page = {value: key for key, value in self.stage_pages.items()}
        self.client = Client(auth=token, notion_version="2025-09-03")

    def _query_all(self, key: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            args: dict[str, Any] = {
                "data_source_id": self.sources[key],
                "page_size": 100,
            }
            if cursor:
                args["start_cursor"] = cursor
            response = self.client.data_sources.query(**args)
            results.extend(response.get("results") or [])
            if not response.get("has_more"):
                return results
            cursor = str(response.get("next_cursor") or "")

    def _entities(self, key: str, entity_type: str, id_name: str) -> list[Entity]:
        output: list[Entity] = []
        for page in self._query_all(key):
            props = page.get("properties") or {}
            status = _select(props.get("Status") or {}) or "draft"
            if status != "active":
                continue
            raw_metadata = _plain(props.get("Metadata JSON") or {})
            try:
                metadata = json.loads(raw_metadata) if raw_metadata else {}
            except json.JSONDecodeError:
                metadata = {}
            source_prop = "Image URL" if entity_type in {"person", "photograph"} else "Source URL"
            output.append(Entity(
                id=_plain(props.get(id_name) or {}),
                type=entity_type,
                title=_plain(props.get("Name") or {}),
                label=_plain(props.get("Label") or {}) if entity_type == "person" else "",
                stage=self.stage_by_page.get(_relation_id(props.get("Stage") or {}), "application"),
                status=status,
                source=str((props.get(source_prop) or {}).get("url") or ""),
                metadata=metadata,
            ))
        return output

    def list_entities(self) -> list[Entity]:
        return (
            self._entities("persons", "person", "Person ID")
            + self._entities("photographs", "photograph", "Photograph ID")
            + self._entities("audio", "audio", "Audio ID")
        )

    def list_relations(self) -> list[Relation]:
        output: list[Relation] = []
        for page in self._query_all("relations"):
            props = page.get("properties") or {}
            if (_select(props.get("Status") or {}) or "draft") != "active":
                continue
            output.append(Relation(
                id=_plain(props.get("Relation ID") or {}),
                source=_plain(props.get("Source ID") or {}),
                target=_plain(props.get("Target ID") or {}),
                type=_plain(props.get("Relation Type") or {}),
                stage=self.stage_by_page.get(_relation_id(props.get("Stage") or {}), "application"),
            ))
        return output

    def list_necessities(self) -> list[Necessity]:
        output: list[Necessity] = []
        for page in self._query_all("necessities"):
            props = page.get("properties") or {}
            output.append(Necessity(
                id=_plain(props.get("Necessity ID") or {}),
                title=_plain(props.get("Name") or {}),
                stage=self.stage_by_page.get(_relation_id(props.get("Stage") or {}), "application"),
                status=_select(props.get("Status") or {}),
                description=_plain(props.get("Description") or {}),
            ))
        return output

    def add_entity(self, entity: Entity) -> Entity:
        mapping = {
            "person": ("persons", "Person ID"),
            "photograph": ("photographs", "Photograph ID"),
            "audio": ("audio", "Audio ID"),
        }
        key, id_name = mapping[entity.type]
        if any(item.id == entity.id for item in self.list_entities()):
            raise ValueError(f"Entity id already exists: {entity.id}")
        props: dict[str, Any] = {
            "Name": {"title": _text(entity.title)},
            id_name: {"rich_text": _text(entity.id)},
            "Status": {"select": {"name": entity.status}},
            "Stage": {"relation": [{"id": self.stage_pages[entity.stage]}]},
            "Metadata JSON": {"rich_text": _text(json.dumps(entity.metadata, ensure_ascii=False))},
            "Created At": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }
        if entity.type == "person":
            props["Label"] = {"rich_text": _text(entity.label)}
            if entity.source:
                props["Image URL"] = {"url": entity.source}
        elif entity.type == "photograph" and entity.source:
            props["Image URL"] = {"url": entity.source}
        elif entity.source:
            props["Source URL"] = {"url": entity.source}
        self.client.pages.create(
            parent={"type": "data_source_id", "data_source_id": self.sources[key]},
            properties=props,
        )
        return entity

