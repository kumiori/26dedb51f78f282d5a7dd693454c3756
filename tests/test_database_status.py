from takeover.database_status import inspect_factory_health, inspect_registry


class EmptyRegistry:
    def list_entities(self):
        return []

    def list_relations(self):
        return []


class BrokenRegistry:
    def list_entities(self):
        raise RuntimeError("private provider detail")

    def list_relations(self):
        raise AssertionError("relations must not be queried after an entity failure")


def test_empty_registry_is_observable_without_becoming_an_error() -> None:
    result = inspect_registry(EmptyRegistry(), "session")

    assert result.status == "empty"
    assert result.authority == "provisional"
    assert result.entity_count == 0
    assert result.relation_count == 0
    assert result.error_type == ""


def test_registry_failure_exposes_only_the_error_type() -> None:
    result = inspect_registry(BrokenRegistry(), "notion")

    assert result.status == "error"
    assert result.authority == "authoritative"
    assert result.entities == ()
    assert result.relations == ()
    assert result.error_type == "RuntimeError"
    assert "private provider detail" not in repr(result)


def test_factory_health_reports_schema_storage_and_duplicate_counts_without_values() -> None:
    class FactoryRegistry(EmptyRegistry):
        def list_players(self):
            return [
                {"player_id": "same", "metadata": {"invitation_capability_hash": "secret-a", "invitation_request_id": "request-a"}},
                {"player_id": "same", "metadata": {"invitation_capability_hash": "secret-a", "invitation_request_id": "request-b"}},
            ]

        def factory_schema_diagnostics(self):
            return {"compatible": True, "missing": 0}

    result = inspect_factory_health(
        FactoryRegistry(),
        "notion",
        storage_probe=lambda: True,
    )

    assert result.notion == "reachable"
    assert result.storage == "reachable"
    assert result.schema == "compatible"
    assert result.duplicate_person_ids == 1
    assert result.duplicate_capability_owners == 1
    assert result.duplicate_invitation_requests == 0
    assert "secret-a" not in repr(result)
