from datetime import datetime, timedelta, timezone

from takeover_engine import Entity, RegistryState, Relation, StorageObject, project_network, project_storage


def test_network_projection_is_interface_neutral() -> None:
    state = RegistryState(
        entities=(Entity("a", "person", "A"), Entity("b", "person", "B"), Entity("c", "person", "C")),
        relations=(Relation("r", "a", "b", "knows"),),
    )
    projection = project_network(state)
    assert projection.isolated_ids == ("c",)


def test_storage_projection_orders_and_accumulates() -> None:
    now = datetime(2026, 8, 20, tzinfo=timezone.utc)
    rows = (
        StorageObject("later", 4, now),
        StorageObject("first", 3, now - timedelta(days=1)),
    )
    points = project_storage(rows)
    assert [(row.object_count, row.total_bytes) for row in points] == [(1, 3), (2, 7)]
