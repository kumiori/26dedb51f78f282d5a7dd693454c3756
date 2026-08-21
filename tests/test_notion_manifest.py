import json
from pathlib import Path

from takeover.notion import NotionRegistry


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_keeps_entity_databases_separate() -> None:
    manifest = json.loads((ROOT / "config" / "takeover_notion.json").read_text())
    assert manifest["status"] == "ready"
    assert {"players", "photographs", "audio"} <= set(manifest["databases"])
    assert manifest["parent_page_url"].endswith("3c08547ffe9a814e919ad2baf9e94f9e")


def test_notion_registry_requires_an_explicit_manifest(tmp_path) -> None:
    missing = tmp_path / "missing.json"
    try:
        NotionRegistry("test-token", missing)
    except FileNotFoundError as exc:
        assert exc.filename == str(missing)
    else:
        raise AssertionError("missing manifests must fail explicitly")


def test_m2_necessities_are_an_exact_structured_corpus() -> None:
    from takeover.registry import NECESSITY_ROWS

    assert NECESSITY_ROWS == (
        ("need-abstract", "abstract", "application", "in_progress"),
        ("need-initial-kernel", "initial_kernel", "application", "found"),
        ("need-material", "material", "application", "collecting"),
        ("need-photographs", "photographs", "application", "found"),
        ("need-translation", "translation", "application", "open"),
        ("need-voices-sound", "voices_sound", "application", "agreed"),
        ("need-application", "application", "application", "to_submit"),
        ("need-production", "production", "production", "not_yet_activated"),
    )
