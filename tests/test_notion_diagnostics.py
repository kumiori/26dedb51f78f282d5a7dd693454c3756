from pathlib import Path

from takeover.notion import NotionRegistry


ROOT = Path(__file__).resolve().parents[1]


def row(status: str) -> dict:
    return {"properties": {"Status": {"select": {"name": status}}}}


class DiagnosticDataSources:
    def __init__(self) -> None:
        self.rows: dict[str, list[dict]] = {}

    def query(self, *, data_source_id, **_kwargs):
        return {"results": self.rows.get(data_source_id, []), "has_more": False}

    def retrieve(self, *, data_source_id):
        return {"properties": self.properties.get(data_source_id, {})}

    properties: dict[str, dict] = {}


class DiagnosticClient:
    def __init__(self) -> None:
        self.data_sources = DiagnosticDataSources()


def test_notion_source_diagnostics_distinguish_raw_and_active_rows() -> None:
    client = DiagnosticClient()
    registry = NotionRegistry(
        "test-token", ROOT / "config" / "takeover_notion.json", client=client
    )
    client.data_sources.rows[registry.sources["players"]] = [row("active"), row("draft")]

    result = {item["source"]: item for item in registry.source_diagnostics()}

    assert result["players"] == {
        "source": "players",
        "status": "connected",
        "rows": 2,
        "active": 1,
        "error": "",
    }
    assert result["relations"]["status"] == "connected"
    assert result["relations"]["rows"] == 0


def test_factory_schema_diagnostics_checks_player_and_relation_contracts() -> None:
    client = DiagnosticClient()
    registry = NotionRegistry(
        "test-token", ROOT / "config" / "takeover_notion.json", client=client
    )
    required = registry.factory_required_properties()
    client.data_sources.properties = {
        registry.sources[source]: {name: {} for name in names}
        for source, names in required.items()
    }

    assert registry.factory_schema_diagnostics() == {"compatible": True, "missing": 0}

    client.data_sources.properties[registry.sources["players"]].pop("Bio")
    assert registry.factory_schema_diagnostics() == {"compatible": False, "missing": 1}
