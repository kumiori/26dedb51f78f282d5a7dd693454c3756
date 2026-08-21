from takeover.graph_3d import build_graph_3d_figure, generated_3d_positions
from takeover.models import Entity, Relation


def test_3d_graph_uses_stable_generated_positions_and_active_relations() -> None:
    entities = [Entity("b", "person", "B"), Entity("a", "person", "A")]
    relation = Relation("r", "a", "b", "collaborates_with")

    assert generated_3d_positions(entities) == generated_3d_positions(list(reversed(entities)))
    figure = build_graph_3d_figure(entities, [relation])

    assert [trace.name for trace in figure.data] == ["relations", "nodes"]
    assert list(figure.data[0].x) == [generated_3d_positions(entities)["a"][0], generated_3d_positions(entities)["b"][0], None]
    assert set(figure.data[1].text) == {"A", "B"}
    assert figure.layout.scene.xaxis.visible is False
