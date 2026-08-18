#!/usr/bin/env python3
"""Create or verify the idempotent Takeover Notion database family.

The manifest is written after every database creation, so an interrupted run
can resume without duplicating completed work.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
from typing import Any

from notion_client import Client

from takeover.registry import NECESSITY_ROWS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "takeover_notion.json"
SCHEMA_VERSION = "takeover-notion-v1"


def rich() -> dict[str, Any]: return {"rich_text": {}}
def number() -> dict[str, Any]: return {"number": {"format": "number"}}
def date_prop() -> dict[str, Any]: return {"date": {}}
def url() -> dict[str, Any]: return {"url": {}}
def select(*options: tuple[str, str]) -> dict[str, Any]:
    return {"select": {"options": [{"name": name, "color": color} for name, color in options]}}


STATUS = select(("draft", "gray"), ("active", "green"), ("dormant", "yellow"), ("archived", "brown"))
DATABASES: dict[str, dict[str, Any]] = {
    "stages": {"title": "Takeover_Stages", "properties": {"Name": {"title": {}}, "Stage ID": rich(), "Order": number(), "Status": select(("dormant", "gray"), ("current", "green"), ("complete", "blue")), "Description": rich()}},
    "persons": {"title": "Takeover_Persons", "properties": {"Name": {"title": {}}, "Person ID": rich(), "Label": rich(), "Status": STATUS, "Image URL": url(), "Metadata JSON": rich(), "Created At": date_prop()}},
    "photographs": {"title": "Takeover_Photographs", "properties": {"Name": {"title": {}}, "Photograph ID": rich(), "Image URL": url(), "Status": STATUS, "Metadata JSON": rich(), "Created At": date_prop()}},
    "audio": {"title": "Takeover_Audio", "properties": {"Name": {"title": {}}, "Audio ID": rich(), "Source URL": url(), "Status": STATUS, "Metadata JSON": rich(), "Created At": date_prop()}},
    "places": {"title": "Takeover_Places", "properties": {"Name": {"title": {}}, "Place ID": rich(), "Description": rich(), "Coordinates": rich(), "Status": STATUS, "Metadata JSON": rich()}},
    "relations": {"title": "Takeover_Relations", "properties": {"Name": {"title": {}}, "Relation ID": rich(), "Source ID": rich(), "Source Type": select(("person", "blue"), ("photograph", "purple"), ("audio", "orange"), ("place", "green"), ("timeline_event", "yellow"), ("necessity", "pink")), "Target ID": rich(), "Target Type": select(("person", "blue"), ("photograph", "purple"), ("audio", "orange"), ("place", "green"), ("timeline_event", "yellow"), ("necessity", "pink")), "Relation Type": rich(), "Status": STATUS, "Metadata JSON": rich(), "Created At": date_prop()}},
    "timeline_events": {"title": "Takeover_TimelineEvents", "properties": {"Name": {"title": {}}, "Event ID": rich(), "Event Type": rich(), "Temporal Position": number(), "Event Date": date_prop(), "Status": select(("planned", "gray"), ("active", "green"), ("realised", "blue"), ("changed", "orange"), ("cancelled", "red")), "Visibility": select(("public", "green"), ("private", "gray")), "Metadata JSON": rich()}},
    "necessities": {"title": "Takeover_Necessities", "properties": {"Name": {"title": {}}, "Necessity ID": rich(), "Status": select(("in_progress", "yellow"), ("found", "green"), ("collecting", "blue"), ("open", "red"), ("agreed", "purple")), "Description": rich(), "Metadata JSON": rich(), "Created At": date_prop()}},
    "interactions": {"title": "Takeover_Interactions", "properties": {"Name": {"title": {}}, "Interaction ID": rich(), "Interaction Type": rich(), "Actor ID": rich(), "Target ID": rich(), "Occurred At": date_prop(), "Visibility": select(("public", "green"), ("private", "gray")), "Metadata JSON": rich()}},
}

RELATIONS: dict[str, dict[str, str]] = {
    "persons": {"Stage": "stages"},
    "places": {"Stages": "stages"},
    "photographs": {"Stage": "stages", "Creators": "persons", "Depicts": "persons", "Place": "places", "Linked Audio": "audio"},
    "audio": {"Stage": "stages", "Speakers": "persons", "Creators": "persons", "Place": "places", "Linked Photographs": "photographs"},
    "timeline_events": {"Stage": "stages", "Related Persons": "persons", "Related Photographs": "photographs", "Related Audio": "audio", "Related Places": "places"},
    "necessities": {"Stage": "stages", "Related Persons": "persons", "Related Photographs": "photographs", "Related Audio": "audio", "Related Places": "places"},
    "interactions": {"Stage": "stages", "Players": "persons", "Related Persons": "persons", "Related Photographs": "photographs", "Related Audio": "audio", "Related Places": "places", "Timeline Event": "timeline_events"},
    "relations": {
        "Stage": "stages", "Source Person": "persons", "Source Photograph": "photographs", "Source Audio": "audio", "Source Place": "places", "Source Timeline Event": "timeline_events", "Source Necessity": "necessities",
        "Target Person": "persons", "Target Photograph": "photographs", "Target Audio": "audio", "Target Place": "places", "Target Timeline Event": "timeline_events", "Target Necessity": "necessities",
    },
}

STAGES = (
    ("application", "Application", 1, "current", "The project is being articulated, assembled and submitted."),
    ("activation", "Activation", 2, "dormant", "The community begins to enter and activate the multiplex."),
    ("production", "Production", 3, "dormant", "Works, encounters and infrastructure are produced."),
    ("exhibition", "Exhibition", 4, "dormant", "The living network becomes publicly present."),
    ("propagation", "Propagation", 5, "dormant", "Connections and materials travel beyond the exhibition."),
)

def text(value: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": value}}]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def save(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def source_id(client: Client, database_id: str, response: dict[str, Any]) -> str:
    sources = response.get("data_sources") or client.databases.retrieve(database_id=database_id).get("data_sources") or []
    if not sources:
        raise RuntimeError(f"No data source returned for {database_id}")
    return str(sources[0]["id"])


def create_database(client: Client, parent_id: str, key: str) -> dict[str, str]:
    spec = DATABASES[key]
    response = client.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=text(spec["title"]),
        description=text("Takeover M1 multiplex community registry."),
        is_inline=False,
        initial_data_source={"properties": spec["properties"]},
    )
    database_id = str(response["id"])
    return {"database_id": database_id, "data_source_id": source_id(client, database_id, response)}


def configure_relations(client: Client, databases: dict[str, Any]) -> None:
    for source_key, relation_map in RELATIONS.items():
        source = str(databases[source_key]["data_source_id"])
        actual = client.data_sources.retrieve(data_source_id=source).get("properties") or {}
        missing = {
            name: {"relation": {"data_source_id": str(databases[target]["data_source_id"]), "single_property": {}}}
            for name, target in relation_map.items() if name not in actual
        }
        if missing:
            client.data_sources.update(data_source_id=source, properties=missing)


def seed_stages(client: Client, manifest: dict[str, Any]) -> None:
    if manifest.get("stage_pages"):
        return
    source = str(manifest["databases"]["stages"]["data_source_id"])
    pages: dict[str, str] = {}
    for stage_id, name, order, status, description in STAGES:
        created = client.pages.create(parent={"type": "data_source_id", "data_source_id": source}, properties={
            "Name": {"title": text(name)}, "Stage ID": {"rich_text": text(stage_id)}, "Order": {"number": order},
            "Status": {"select": {"name": status}}, "Description": {"rich_text": text(description)},
        })
        pages[stage_id] = str(created["id"])
    manifest["stage_pages"] = pages


def sync_necessities(client: Client, manifest: dict[str, Any]) -> None:
    """Make the live Necessities data source exactly match the M2 corpus."""
    source = str(manifest["databases"]["necessities"]["data_source_id"])
    stage_id = str(manifest["stage_pages"]["application"])
    client.data_sources.update(data_source_id=source, properties={"Status": DATABASES["necessities"]["properties"]["Status"]})
    response = client.data_sources.query(data_source_id=source, page_size=100)
    existing = {
        "".join(part.get("plain_text") or "" for part in ((page.get("properties") or {}).get("Necessity ID") or {}).get("rich_text") or []): page
        for page in response.get("results") or []
    }
    current_ids = {row[0] for row in NECESSITY_ROWS}
    for item_id, name, status in NECESSITY_ROWS:
        properties = {
            "Name": {"title": text(name)}, "Necessity ID": {"rich_text": text(item_id)},
            "Status": {"select": {"name": status}}, "Description": {"rich_text": []},
            "Stage": {"relation": [{"id": stage_id}]},
        }
        page = existing.get(item_id)
        if page:
            client.pages.update(page_id=page["id"], properties=properties, archived=False)
        else:
            properties["Created At"] = {"date": {"start": date.today().isoformat()}}
            client.pages.create(parent={"type": "data_source_id", "data_source_id": source}, properties=properties)
    for item_id, page in existing.items():
        if item_id and item_id not in current_ids:
            client.pages.update(page_id=page["id"], archived=True)
    manifest["necessities_seeded"] = True
    manifest["necessities_version"] = "m2.0"


def verify(client: Client, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    databases = manifest.get("databases") or {}
    for key, spec in DATABASES.items():
        if key not in databases:
            errors.append(f"missing database: {key}")
            continue
        props = client.data_sources.retrieve(data_source_id=databases[key]["data_source_id"]).get("properties") or {}
        for name in spec["properties"]:
            if name not in props:
                errors.append(f"{key}.{name}: missing")
        for name in RELATIONS.get(key, {}):
            if (props.get(name) or {}).get("type") != "relation":
                errors.append(f"{key}.{name}: missing relation")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "create", "sync-necessities", "verify"))
    parser.add_argument("--parent-page-id", default="")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    args = parser.parse_args()
    if args.command == "plan":
        for key, spec in DATABASES.items(): print(f"{key}: {spec['title']}")
        return
    token = os.getenv("NOTION_TOKEN", "").strip()
    if not token:
        raise RuntimeError("NOTION_TOKEN is required")
    client = Client(auth=token, notion_version="2025-09-03")
    path = Path(args.manifest).resolve()
    manifest = load(path)
    if args.command == "create":
        parent_id = args.parent_page_id or str(manifest.get("parent_page_id") or "")
        if not parent_id:
            raise RuntimeError("Provide --parent-page-id for the Takeover page")
        manifest.setdefault("schema_version", SCHEMA_VERSION)
        manifest.setdefault("parent_page_id", parent_id)
        manifest.setdefault("databases", {})
        if manifest["parent_page_id"] != parent_id:
            raise RuntimeError("Manifest parent does not match requested parent")
        for key in DATABASES:
            if key not in manifest["databases"]:
                manifest["databases"][key] = create_database(client, parent_id, key)
                save(path, manifest)
        configure_relations(client, manifest["databases"])
        seed_stages(client, manifest)
        sync_necessities(client, manifest)
        manifest["status"] = "ready"
        save(path, manifest)
    elif args.command == "sync-necessities":
        sync_necessities(client, manifest)
        save(path, manifest)
    errors = verify(client, manifest)
    if errors:
        raise RuntimeError("Verification failed:\n- " + "\n- ".join(errors))
    print(f"verified {len(DATABASES)} databases ({SCHEMA_VERSION})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
