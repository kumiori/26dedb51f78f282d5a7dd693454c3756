import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_keeps_entity_databases_separate() -> None:
    manifest = json.loads((ROOT / "config" / "takeover_notion.json").read_text())
    assert manifest["status"] == "ready"
    assert {"persons", "photographs", "audio"} <= set(manifest["databases"])
    assert manifest["parent_page_url"].endswith("3c08547ffe9a814e919ad2baf9e94f9e")

