from takeover.models import Entity
from takeover.registry import SessionRegistry


def test_entity_types_are_not_flattened() -> None:
    assert Entity("ave", "person", "Ave", "artist").type == "person"
    assert Entity("photo-1", "photograph", "Untitled").type == "photograph"
    assert Entity("audio-1", "audio", "Field recording").type == "audio"


def test_stage_is_explicit_and_validated() -> None:
    entity = Entity("ave", "person", "Ave", stage="application")
    assert entity.stage == "application"


def test_unknown_entity_type_is_rejected() -> None:
    try:
        Entity("generic", "node", "Generic node")
    except ValueError as exc:
        assert "Unsupported entity type" in str(exc)
    else:
        raise AssertionError("generic graph nodes must not be admitted")


def test_fallback_necessities_keep_semantic_ids_out_of_presentation() -> None:
    items = SessionRegistry({}).list_necessities()
    assert [item.title for item in items] == [
        "abstract", "material", "initial_kernel", "photographs", "voices_sound", "translation"
    ]
    assert [item.status for item in items] == [
        "in_progress", "collecting", "found", "found", "agreed", "open"
    ]
