from takeover.graph import build_graph_html
from takeover.models import Entity, Relation


def test_empty_graph_exposes_only_start_hub() -> None:
    html = build_graph_html([], [])
    assert "START HERE" in html
    assert 'class="node ' not in html


def test_typed_entity_and_relation_are_rendered() -> None:
    entities = [Entity("ave", "person", "Ave", "artist"), Entity("image", "photograph", "Image")]
    html = build_graph_html(entities, [Relation("r1", "ave", "image", "created")])
    assert "person" in html
    assert "photograph" in html
    assert "created" in html

