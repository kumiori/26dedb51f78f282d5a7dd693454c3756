from pathlib import Path

import pytest

from takeover.resource_field import load_resource_field, resource_rows


ROOT = Path(__file__).resolve().parents[1]


def test_resource_field_preserves_states_and_live_values() -> None:
    payload = load_resource_field(ROOT / "config" / "takeover_resource_field.yaml")
    rows = resource_rows(payload, active_people=4, bucket_bytes=1024 * 1024, bucket_files=2, activation_events=1)
    indexed = {row["id"]: row for row in rows}
    assert payload["application"] == {"state": "open", "submitted_at": None}
    assert indexed["people"]["value"] == "4 ACTIVE"
    assert indexed["money"]["state"] == "intention"
    assert indexed["storage"]["value"] == "1.00 MB · 2 FILES"
    assert indexed["attention"]["value"] == "1 SESSION ACTIVATIONS"


def test_submitted_state_requires_a_timestamp(tmp_path) -> None:
    path = tmp_path / "field.yaml"
    path.write_text("schema_version: takeover-resource-field/v1\napplication: {state: submitted, submitted_at: null}\nresources: [{id: x, state: open}]\n")
    with pytest.raises(ValueError, match="timestamp"):
        load_resource_field(path)
