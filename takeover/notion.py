"""Notion-backed registry for the Takeover database family."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
from typing import Any

from notion_client import Client

from .models import Entity, Necessity, Relation
from .node_population import PlayerPopulation
from .player_invitations import CapabilityResolution


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
    def __init__(self, token: str, manifest_path: Path, *, client: Any | None = None) -> None:
        """Create a registry from an explicit, application-owned manifest."""
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.sources = {
            key: value["data_source_id"]
            for key, value in self.manifest["databases"].items()
        }
        self.stage_pages = dict(self.manifest["stage_pages"])
        self.stage_by_page = {value: key for key, value in self.stage_pages.items()}
        self.client = client or Client(auth=token, notion_version="2025-09-03")

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

    @staticmethod
    def factory_required_properties() -> dict[str, tuple[str, ...]]:
        return {
            "players": (
                "Name", "Person ID", "Label", "Image URL", "Bio", "Practice",
                "Sample URL", "Metadata JSON", "Stage", "Status", "Network State",
                "Visibility",
            ),
            "relations": (
                "Name", "Relation ID", "Source ID", "Source Type", "Source Person",
                "Target ID", "Target Type", "Target Person", "Relation Type", "Stage",
                "Status", "Metadata JSON",
            ),
        }

    def factory_schema_diagnostics(self) -> dict[str, Any]:
        """Check only the property names needed by the player factory contract."""
        missing = 0
        for source, required in self.factory_required_properties().items():
            response = self.client.data_sources.retrieve(
                data_source_id=self.sources[source]
            )
            available = set((response.get("properties") or {}).keys())
            missing += len(set(required) - available)
        return {"compatible": missing == 0, "missing": missing}

    def source_diagnostics(self) -> list[dict[str, Any]]:
        """Return safe row counts for read-only operator diagnostics."""
        output: list[dict[str, Any]] = []
        for key in ("players", "photographs", "audio", "relations", "necessities"):
            try:
                rows = self._query_all(key)
                active = sum(
                    (_select((row.get("properties") or {}).get("Status") or {}) or "draft")
                    == "active"
                    for row in rows
                )
                output.append({
                    "source": key,
                    "status": "connected",
                    "rows": len(rows),
                    "active": active,
                    "error": "",
                })
            except Exception as exc:
                output.append({
                    "source": key,
                    "status": "error",
                    "rows": 0,
                    "active": 0,
                    "error": type(exc).__name__,
                })
        return output

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
            # Authentication verifiers are adapter-private and never enter graph projections.
            metadata.pop("invitation_capability_hash", None)
            source_prop = "Image URL" if entity_type in {"person", "photograph"} else "Source URL"
            source = str((props.get(source_prop) or {}).get("url") or "")
            if entity_type == "person":
                network_state = _select(props.get("Network State") or {}) or "active"
                visibility = _select(props.get("Visibility") or {}) or "public"
                metadata = {
                    **metadata,
                    "bio": _plain(props.get("Bio") or {}),
                    "practice": _plain(props.get("Practice") or {}),
                    "sample_url": str((props.get("Sample URL") or {}).get("url") or ""),
                    "avatar": {"url": source} if source else {},
                    "registry_status": status,
                    "visibility": visibility,
                }
                if visibility != "public":
                    source = ""
                    metadata = {
                        "node_stage": metadata.get("node_stage", "latent"),
                        "registry_status": status,
                        "visibility": visibility,
                    }
                title = _plain(props.get("Name") or {}) if visibility == "public" else ("PRIVATE" if visibility == "private" else "UNKNOWN")
                label = _plain(props.get("Label") or {}) if visibility == "public" else ""
                entity_status = network_state
            else:
                title = _plain(props.get("Name") or {})
                label = ""
                entity_status = status
            output.append(Entity(
                id=_plain(props.get(id_name) or {}),
                type=entity_type,
                title=title,
                label=label,
                stage=self.stage_by_page.get(_relation_id(props.get("Stage") or {}), "application"),
                status=entity_status,
                source=source,
                metadata=metadata,
            ))
        return output

    def list_entities(self) -> list[Entity]:
        return (
            self._entities("players", "person", "Person ID")
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
                status=_select(props.get("Status") or {}) or "active",
                metadata=(
                    json.loads(_plain(props.get("Metadata JSON") or {}))
                    if _plain(props.get("Metadata JSON") or {}) else {}
                ),
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
            "person": ("players", "Person ID"),
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

    def _player_rows(self, person_id: str) -> list[dict[str, Any]]:
        response = self.client.data_sources.query(
            data_source_id=self.sources["players"],
            filter={"property": "Person ID", "rich_text": {"equals": person_id}},
            page_size=100,
        )
        return list(response.get("results") or [])

    def _player_from_page(self, page: dict[str, Any]) -> dict[str, Any]:
        props = page.get("properties") or {}
        raw_metadata = _plain(props.get("Metadata JSON") or {})
        return {
            "page_id": str(page.get("id") or ""),
            "player_id": _plain(props.get("Person ID") or {}),
            "name": _plain(props.get("Name") or {}),
            "label": _plain(props.get("Label") or {}),
            "image_url": str((props.get("Image URL") or {}).get("url") or ""),
            "bio": _plain(props.get("Bio") or {}),
            "practice": _plain(props.get("Practice") or {}),
            "sample_url": str((props.get("Sample URL") or {}).get("url") or ""),
            "metadata": json.loads(raw_metadata) if raw_metadata else {},
            "initial_condition": (json.loads(raw_metadata).get("initial_condition") if raw_metadata else {}) or {},
            "project_stage": self.stage_by_page.get(_relation_id(props.get("Stage") or {}), ""),
            "status": _select(props.get("Status") or {}),
            "network_state": _select(props.get("Network State") or {}) or "active",
            "visibility": _select(props.get("Visibility") or {}) or "public",
        }

    def count_players(self, person_id: str) -> int:
        return len(self._player_rows(person_id))

    def list_players(self) -> list[dict[str, Any]]:
        """Read all player rows as application-level records."""
        return [self._player_from_page(page) for page in self._query_all("players")]

    def read_player(self, person_id: str) -> dict[str, Any] | None:
        """Read one player by stable Person ID without modifying Notion."""
        matches = self._player_rows(person_id)
        if not matches:
            return None
        row = self._player_from_page(matches[0])
        row["row_count"] = len(matches)
        row["duplicates"] = max(0, len(matches) - 1)
        return row

    def resolve_player_invitation(self, code: str, capability: str) -> dict[str, Any] | None:
        """Resolve one invitation without exposing its verifier through graph entities."""
        candidate_code = code.strip().upper()
        candidate_hash = hashlib.sha256(capability.strip().encode("utf-8")).hexdigest()
        matches = []
        for page in self._query_all("players"):
            row = self._player_from_page(page)
            metadata = row.get("metadata") or {}
            expected_code = str(metadata.get("invitation_code") or "").upper()
            expected_hash = str(metadata.get("invitation_capability_hash") or "")
            if expected_code == candidate_code and expected_hash and secrets.compare_digest(expected_hash, candidate_hash):
                matches.append(row)
        return matches[0] if len(matches) == 1 else None

    def resolve_unfinished_player_capability(self, capability: str) -> dict[str, Any] | None:
        """Resolve one capability only while its player node remains unfinished."""
        candidate_hash = hashlib.sha256(capability.strip().encode("utf-8")).hexdigest()
        matches = []
        for page in self._query_all("players"):
            row = self._player_from_page(page)
            metadata = row.get("metadata") or {}
            expected_hash = str(metadata.get("invitation_capability_hash") or "")
            node_stage = str(metadata.get("node_stage") or "")
            if (
                row.get("status") == "active"
                and node_stage in {"invited", "node_population"}
                and expected_hash
                and secrets.compare_digest(expected_hash, candidate_hash)
            ):
                matches.append(row)
        return matches[0] if len(matches) == 1 else None

    def resolve_player_capability(self, capability: str) -> CapabilityResolution:
        """Resolve one player-scoped capability with an explicit ownership outcome."""
        candidate = capability.strip()
        if not candidate:
            return CapabilityResolution("invalid")
        candidate_hash = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        matches = []
        for page in self._query_all("players"):
            row = self._player_from_page(page)
            expected_hash = str((row.get("metadata") or {}).get("invitation_capability_hash") or "")
            if expected_hash and secrets.compare_digest(expected_hash, candidate_hash):
                matches.append(row)
        if not matches:
            return CapabilityResolution("invalid")
        if len(matches) != 1:
            return CapabilityResolution("duplicate", matches=len(matches))
        return CapabilityResolution("resolved", player=matches[0], matches=1)

    def upsert_player(self, payload: PlayerPopulation) -> dict[str, Any]:
        """Create or update one player by stable Person ID, then read it back."""
        if payload.project_stage not in self.stage_pages:
            raise ValueError(f"Unknown project stage: {payload.project_stage}")
        source = self.sources["players"]
        matches = self._player_rows(payload.player_id)
        if len(matches) > 1:
            raise ValueError(f"Duplicate Person ID in Takeover_Players: {payload.player_id}")
        existing_metadata: dict[str, Any] = {}
        if matches:
            raw_existing = _plain((matches[0].get("properties") or {}).get("Metadata JSON") or {})
            existing_metadata = json.loads(raw_existing) if raw_existing else {}
        existing_initial = existing_metadata.get("initial_condition") or {}
        if existing_initial and payload.initial_condition and existing_initial != payload.initial_condition:
            raise ValueError("Initial condition is immutable for an existing player.")
        metadata = {
            **{key: value for key, value in payload.metadata.items() if key != "initial_condition"},
            "node_stage": payload.node_stage,
        }
        initial_condition = existing_initial or payload.initial_condition
        if initial_condition:
            metadata["initial_condition"] = initial_condition
        properties: dict[str, Any] = {
            "Name": {"title": _text(payload.name)},
            "Person ID": {"rich_text": _text(payload.player_id)},
            "Label": {"rich_text": _text(payload.label)},
            "Image URL": {"url": payload.image_url or None},
            "Bio": {"rich_text": _text(payload.bio)},
            "Practice": {"rich_text": _text(payload.practice)},
            "Sample URL": {"url": payload.sample_url or None},
            "Metadata JSON": {"rich_text": _text(json.dumps(metadata, ensure_ascii=False))},
            "Stage": {"relation": [{"id": self.stage_pages[payload.project_stage]}]},
            "Status": {"select": {"name": payload.status}},
            "Network State": {"select": {"name": payload.network_state}},
            "Visibility": {"select": {"name": payload.visibility}},
        }
        if matches:
            action = "UPDATED"
            page_id = str(matches[0]["id"])
            self.client.pages.update(page_id=page_id, properties=properties, archived=False)
        else:
            action = "CREATED"
            properties["Created At"] = {"date": {"start": datetime.now(timezone.utc).isoformat()}}
            created = self.client.pages.create(
                parent={"type": "data_source_id", "data_source_id": source}, properties=properties,
            )
            page_id = str(created["id"])
        page = self.client.pages.retrieve(page_id=page_id)
        row = self._player_from_page(page)
        row["action"] = action
        row["row_count"] = self.count_players(payload.player_id)
        row["duplicates"] = max(0, row["row_count"] - 1)
        return row

    def upsert_player_relation(self, relation: Relation) -> dict[str, Any]:
        """Create or update one person-to-person graph relation, then read it back."""
        if relation.stage not in self.stage_pages:
            raise ValueError(f"Unknown project stage: {relation.stage}")
        source_players = self._player_rows(relation.source)
        target_players = self._player_rows(relation.target)
        if len(source_players) != 1 or len(target_players) != 1:
            raise ValueError("Relation endpoints must each resolve to exactly one player.")
        response = self.client.data_sources.query(
            data_source_id=self.sources["relations"],
            filter={"property": "Relation ID", "rich_text": {"equals": relation.id}},
            page_size=2,
        )
        matches = list(response.get("results") or [])
        if len(matches) > 1:
            raise ValueError(f"Duplicate Relation ID in Takeover_Relations: {relation.id}")
        properties: dict[str, Any] = {
            "Name": {"title": _text(f"{relation.source} · {relation.type} · {relation.target}")},
            "Relation ID": {"rich_text": _text(relation.id)},
            "Source ID": {"rich_text": _text(relation.source)},
            "Source Type": {"select": {"name": "person"}},
            "Source Person": {"relation": [{"id": source_players[0]["id"]}]},
            "Target ID": {"rich_text": _text(relation.target)},
            "Target Type": {"select": {"name": "person"}},
            "Target Person": {"relation": [{"id": target_players[0]["id"]}]},
            "Relation Type": {"rich_text": _text(relation.type)},
            "Stage": {"relation": [{"id": self.stage_pages[relation.stage]}]},
            "Status": {"select": {"name": relation.status}},
            "Metadata JSON": {
                "rich_text": _text(json.dumps(relation.metadata, ensure_ascii=False))
                if relation.metadata else []
            },
        }
        if matches:
            action = "UPDATED"
            page_id = str(matches[0]["id"])
            self.client.pages.update(page_id=page_id, properties=properties, archived=False)
        else:
            action = "CREATED"
            properties["Created At"] = {"date": {"start": datetime.now(timezone.utc).isoformat()}}
            created = self.client.pages.create(
                parent={"type": "data_source_id", "data_source_id": self.sources["relations"]},
                properties=properties,
            )
            page_id = str(created["id"])
        page = self.client.pages.retrieve(page_id=page_id)
        props = page.get("properties") or {}
        return {
            "action": action,
            "page_id": page_id,
            "relation_id": _plain(props.get("Relation ID") or {}),
            "source": _plain(props.get("Source ID") or {}),
            "target": _plain(props.get("Target ID") or {}),
            "type": _plain(props.get("Relation Type") or {}),
            "stage": self.stage_by_page.get(_relation_id(props.get("Stage") or {}), ""),
            "status": _select(props.get("Status") or {}),
            "metadata": (
                json.loads(_plain(props.get("Metadata JSON") or {}))
                if _plain(props.get("Metadata JSON") or {}) else {}
            ),
        }
