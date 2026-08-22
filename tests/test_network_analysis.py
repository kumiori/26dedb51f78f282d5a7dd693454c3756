from datetime import datetime, timezone

from takeover.models import Entity, Relation
from takeover.network_analysis import connectivity_history, multiplex_3d_figure, multiplex_statistics


def test_connectivity_history_uses_observed_creation_times_cumulatively() -> None:
    entities = [
        Entity("a", "person", "A", metadata={"created_at": "2026-08-20T00:00:00+00:00"}),
        Entity("b", "person", "B", metadata={"created_at": "2026-08-21T00:00:00+00:00"}),
    ]
    relations = [Relation(
        "r", "a", "b", "invited",
        metadata={"created_at": "2026-08-21T12:00:00+00:00"},
    )]

    rows = connectivity_history(
        entities, relations, now=datetime(2026, 8, 22, tzinfo=timezone.utc),
    )

    assert [(row["nodes"], row["relations"]) for row in rows] == [
        (1, 0), (2, 0), (2, 1), (2, 1),
    ]
    assert rows[-1]["connectivity"] == 1.0


def test_multiplex_statistics_and_3d_projection_keep_relation_layers_separate() -> None:
    entities = [Entity("a", "person", "A"), Entity("b", "person", "B"), Entity("c", "person", "C")]
    relations = [
        Relation("r1", "a", "b", "invited"),
        Relation("r2", "a", "b", "collaborates_with"),
    ]

    summary, layers = multiplex_statistics(entities, relations)
    figure = multiplex_3d_figure(entities, relations)

    assert summary["nodes"] == 3
    assert summary["relations"] == 2
    assert summary["layers"] == 2
    assert summary["mean_layers_per_dyad"] == 2.0
    assert summary["mean_node_layer_participation"] == 2 / 3
    assert {row["layer"] for row in layers} == {"invited", "collaborates_with"}
    assert {trace.name for trace in figure.data} == {
        "invited · relations", "invited · nodes",
        "collaborates_with · relations", "collaborates_with · nodes",
    }
