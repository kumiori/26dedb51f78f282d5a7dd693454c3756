import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_keeps_entity_databases_separate() -> None:
    manifest = json.loads((ROOT / "config" / "takeover_notion.json").read_text())
    assert manifest["status"] == "ready"
    assert {"persons", "photographs", "audio"} <= set(manifest["databases"])
    assert manifest["parent_page_url"].endswith("3c08547ffe9a814e919ad2baf9e94f9e")


def test_m2_necessities_are_an_exact_structured_corpus() -> None:
    from takeover.registry import NECESSITY_ROWS

    assert NECESSITY_ROWS == (
        ("need-abstract", "abstract", "in_progress"),
        ("need-initial-kernel", "initial_kernel", "found"),
        ("need-material", "material", "collecting"),
        ("need-photographs", "photographs", "found"),
        ("need-translation", "translation", "open"),
        ("need-voices-sound", "voices_sound", "agreed"),
    )
