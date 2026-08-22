from pathlib import Path

import httpx
from notion_client.errors import APIErrorCode, APIResponseError

from takeover.notion import NotionRegistry, safe_notion_error


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
        self.users = DiagnosticUsers()


class DiagnosticUsers:
    def me(self):
        return {"type": "bot"}


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
    assert result["interactions"]["status"] == "connected"
    assert result["interactions"]["rows"] == 0


def test_connection_diagnostics_separate_auth_source_access_and_query() -> None:
    registry = NotionRegistry(
        "test-token", ROOT / "config" / "takeover_notion.json", client=DiagnosticClient()
    )

    assert [item["status"] for item in registry.connection_diagnostics()] == [
        "pass", "pass", "pass"
    ]


def test_safe_notion_error_reports_provider_status_without_response_body() -> None:
    error = APIResponseError(
        code=APIErrorCode.ObjectNotFound,
        status=404,
        message="Object abc-secret-id was not found",
        headers=httpx.Headers(),
        raw_body_text='{"object": "error"}',
    )

    assert safe_notion_error(error) == {
        "error_type": "APIResponseError",
        "http_status": "404",
        "provider_code": "object_not_found",
        "diagnosis": "SOURCE NOT SHARED OR MANIFEST MISMATCH",
    }


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
