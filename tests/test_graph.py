import re

from takeover.graph import build_graph_html, clipped_segment, generated_positions
from takeover.models import Entity, Relation
from takeover.registry import PRESEED_ENTITIES, SEED_ENTITIES, SEED_RELATIONS, with_rc0_seeds


def test_empty_graph_exposes_only_start_hub() -> None:
    html = build_graph_html([], [])
    assert "START HERE" in html
    assert 'class="node ' not in html
    assert 'class="ghost"' not in html
    assert 'class="hub"' in html
    assert 'class="you-orb"' not in html
    assert ".hub:hover,.hub:focus { background:#777168" in html
    assert "top:50%" in html
    ratio = re.search(r"<b>([^<]+)</b> CONNECTIVITY", html)
    assert ratio and ratio.group(1) == "0.00"
    assert build_graph_html([], []) == html


def test_state_summary_has_a_dedicated_band_outside_the_graph_field() -> None:
    html = build_graph_html([Entity("ave", "person", "Ave")], [])

    assert 'class="graph-shell"' in html
    field_end = html.index("</div>", html.index('class="field"'))
    assert field_end < html.index('class="stats"')
    assert ".stats { position:relative" in html
    assert ".stats { position:absolute" not in html


def test_generated_layout_is_stable_and_requires_no_stored_coordinates() -> None:
    entities = [Entity("b", "person", "B"), Entity("a", "person", "A"), Entity("c", "person", "C")]
    first = generated_positions(entities)
    second = generated_positions(list(reversed(entities)))
    assert first == second
    assert set(first) == {"a", "b", "c"}
    assert all(0 < x < 1 and 0 < y < 1 for x, y in first.values())


def test_edges_are_clipped_to_circular_node_boundaries() -> None:
    assert clipped_segment((0, 0), (10, 0), 2, 3) == (2, 0, 7, 0)

    diagonal = clipped_segment((0, 0), (10, 10), 2, 2)
    assert diagonal[0] > 0 and diagonal[1] > 0
    assert diagonal[2] < 10 and diagonal[3] < 10


def test_typed_entity_and_relation_are_rendered() -> None:
    entities = [Entity("ave", "person", "Ave", "artist"), Entity("image", "photograph", "Image")]
    html = build_graph_html(entities, [Relation("r1", "ave", "image", "created")])
    assert "person" in html
    assert "photograph" in html
    assert "created" in html
    assert "1.00" in html


def test_ready_node_avatar_is_a_renderer_level_circular_image() -> None:
    entity = Entity(
        "ave", "person", "Ave",
        metadata={"node_stage": "ready", "avatar": {"url": "https://example.test/original.jpg", "crop": {"x": 0.4, "y": 0.6, "scale": 1.2}}},
    )
    html = build_graph_html([entity], [])
    assert "inhabited-node-avatar" in html
    assert "https://example.test/original.jpg" in html
    assert "border-radius:50%" in html


def test_participant_context_survives_clicking_their_graph_node() -> None:
    entities = [
        Entity("mai_brit", "person", "Mai-Brit", metadata={"node_stage": "node_population"}),
        Entity("ave", "person", "Ave", metadata={"node_stage": "node_population"}),
    ]
    html = build_graph_html(
        entities, [], editable_node_id="mai_brit", write_capability="secret / value",
    )
    assert '?view=network&amp;node=mai_brit&amp;a=mai_brit&amp;c=secret%20%2F%20value' in html
    assert 'node=ave&amp;a=mai_brit&amp;c=' not in html
    assert "context-node" in html


def test_rc0_graph_has_depth_structured_social_seed() -> None:
    entities, relations = with_rc0_seeds([], [])
    html = build_graph_html(entities, relations)

    assert [entity.title for entity in entities[:4]] == ["kumiori", "Ave", "Mai-Brit", "Kenn-Eerik"]
    assert entities[3].id == "kenneerik"
    assert [entity.metadata["node_stage"] for entity in entities[:4]] == [
        "node_population", "node_population", "node_population", "node_population",
    ]
    assert PRESEED_ENTITIES[0].metadata["node_stage"] == "node_population"
    assert PRESEED_ENTITIES[1].metadata["node_stage"] == "invited"
    assert [entity.status for entity in entities] == [
        "active", "active", "active", "active",
        "latent_known", "latent_private", "unknown", "unknown",
    ]
    assert PRESEED_ENTITIES[0].title == "Graziano"
    assert "Graziano" in html
    assert "Michela" not in html
    assert "latent_01" not in html and "latent_02" not in html
    assert {relation.type for relation in relations} == {"collaborates_with"}
    assert all(relation.source != "*" and relation.target != "*" for relation in SEED_RELATIONS)
    assert html.count('class="relation-stroke"') == 4
    assert html.count('class="relation-link"') == 4
    assert "ENTER THE NETWORK" not in html
    assert "STATE OF THE ART" in html
    assert "ACTIVE RELATIONS" in html
    assert "Inspect collaborates_with relation" in html
    assert "4</b> ACTIVE" in html
    assert "1</b> LATENT KNOWN" in html
    assert "1</b> LATENT PRIVATE" in html
    assert "2</b> UNKNOWN" in html
    assert 'class="node depth-node latent-known person"' in html
    assert 'class="node depth-node latent-private person"' in html
    assert html.count('class="node depth-node unknown person"') == 2
    assert "Person • Alien · artist · application" in html
    assert "artist · application" in html


def test_rc0_seed_overlay_does_not_duplicate_registry_rows() -> None:
    entities, relations = with_rc0_seeds([SEED_ENTITIES[0]], [SEED_RELATIONS[0]])
    assert sum(entity.id == "kumiori" for entity in entities) == 1
    assert sum(relation.id == "seed-kumiori-ave" for relation in relations) == 1
