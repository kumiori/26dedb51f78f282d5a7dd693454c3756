from datetime import datetime, timezone

import pytest

from takeover_engine import Entity, Event, RegistryState, Relation, Visibility


def test_domain_records_validate_and_normalize() -> None:
    entity = Entity("person-1", "person", "A person", visibility="private")
    assert entity.type == "person"
    assert entity.visibility is Visibility.PRIVATE
    event = Event("event-1", "opened", datetime.now(timezone.utc))
    assert event.occurred_at.tzinfo is timezone.utc


def test_registry_rejects_dangling_relations() -> None:
    with pytest.raises(ValueError, match="endpoints"):
        RegistryState(relations=(Relation("r", "missing-a", "missing-b", "knows"),))
