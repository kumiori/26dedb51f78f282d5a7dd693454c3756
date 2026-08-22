#!/usr/bin/env python3
"""Migrate legacy Streamlit capabilities into authoritative Notion player rows."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import tomllib

from takeover.capability_migration import CapabilityMigrationError, migrate_legacy_capabilities
from takeover.notion import NotionRegistry


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secrets", type=Path, default=ROOT / ".streamlit" / "secrets.toml")
    parser.add_argument(
        "--mapping",
        type=Path,
        help="Optional JSON object mapping legacy identity aliases to canonical Person IDs.",
    )
    parser.add_argument(
        "--inspect-players",
        action="store_true",
        help="Read-only: list player names and canonical Person IDs; never show metadata.",
    )
    parser.add_argument("--apply", action="store_true", help="Required acknowledgement for live writes.")
    args = parser.parse_args()
    if not args.apply and not args.inspect_players:
        print("REFUSED · pass --apply to write to the live Takeover_Players database")
        return 2
    payload = tomllib.loads(args.secrets.read_text(encoding="utf-8"))
    notion = payload.get("notion") or {}
    token = str(
        os.getenv("NOTION_TOKEN", "")
        or payload.get("NOTION_TOKEN", "")
        or notion.get("token", "")
        or notion.get("api_key", "")
    ).strip()
    if not token:
        print("PLAYER REGISTRY UNAVAILABLE · Notion credential is not configured")
        return 2
    identities = payload.get("takeover_identities") or {}
    mapping = json.loads(args.mapping.read_text(encoding="utf-8")) if args.mapping else None
    store = NotionRegistry(token, ROOT / "config" / "takeover_notion.json")
    if args.inspect_players:
        try:
            players = sorted(
                store.list_players(),
                key=lambda row: (str(row.get("name") or "").casefold(), str(row.get("player_id") or "")),
            )
        except Exception as exc:
            print(f"PLAYER REGISTRY DEGRADED · {type(exc).__name__}")
            return 2
        print("NAME\tPERSON ID")
        for player in players:
            print(f'{str(player.get("name") or "")}\t{str(player.get("player_id") or "")}')
        print(f"{len(players)} PLAYERS")
        return 0
    try:
        report = migrate_legacy_capabilities(
            store,
            identities,
            mapping=mapping,
            clock=lambda: datetime.now(timezone.utc),
        )
    except CapabilityMigrationError as exc:
        print(f"MIGRATION REFUSED · {exc}")
        return 1
    except Exception as exc:
        print(f"PLAYER REGISTRY DEGRADED · {type(exc).__name__}")
        return 2
    for line in report.lines:
        print(line)
    print(
        f"{report.migrated + report.verified} MIGRATED OR VERIFIED · "
        f"{report.skipped} SKIPPED · {report.total} IDENTITIES"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
