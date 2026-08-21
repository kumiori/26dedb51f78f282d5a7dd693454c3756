from datetime import datetime, timezone
from pathlib import Path

import pytest

from takeover.models import Entity
from takeover.inhabited_nodes import FileNodeStore, NODE_STAGES, NodeStore, PublicNodeMediaStore, apply_inhabited_nodes, node_stage


def test_seeded_node_population_stage_is_controlled_registry_state() -> None:
    entity = Entity("ave", "person", "Ave", metadata={"node_stage": "node_population"})
    assert "node_population" in NODE_STAGES
    assert node_stage(entity) == "node_population"
    with pytest.raises(ValueError, match="Unsupported node stage"):
        node_stage(Entity("x", "person", "X", metadata={"node_stage": "mystery"}))


def test_inhabited_node_keeps_original_avatar_crop_and_one_public_sample() -> None:
    state = {}
    store = NodeStore(state)
    record = store.save(
        node_id="ave",
        avatar={"url": "https://example.test/portrait.jpg", "filename": "portrait.jpg", "crop": {"x": 0.4, "y": 0.6, "scale": 1.2}},
        text="Image maker.",
        practice=["photography", "cyanotype"],
        sample={"type": "image", "url": "https://example.test/work.jpg", "caption": "One work"},
        clock=lambda: datetime(2026, 8, 21, 10, tzinfo=timezone.utc),
    )

    assert record["node"]["avatar"]["filename"] == "portrait.jpg"
    assert record["node"]["avatar"]["crop"] == {"x": 0.4, "y": 0.6, "scale": 1.2}
    assert record["state"]["inhabited"] is True
    assert record["state"]["complete"] is True
    assert record["stage"] == "ready"
    assert len([record["node"]["sample"]]) == 1

    enriched = apply_inhabited_nodes(
        [Entity("ave", "person", "Ave", metadata={"node_stage": "node_population"})],
        store.list_nodes(),
    )[0]
    assert enriched.metadata["node_stage"] == "ready"
    assert enriched.metadata["avatar"]["url"].endswith("portrait.jpg")


def test_file_node_store_locks_a_completed_node_and_media_keeps_original(tmp_path) -> None:
    media = PublicNodeMediaStore(tmp_path / "media")
    avatar = media.save_original(node_id="ave", filename="portrait.jpg", content_type="image/jpeg", data=b"original-image")
    assert Path(avatar["path"]).read_bytes() == b"original-image"
    store = FileNodeStore(tmp_path / "nodes.json")
    record = store.save(
        node_id="ave", avatar={**avatar, "crop": {"x": .5, "y": .5, "scale": 1}},
        text="Bio", practice=["cyanotype"], sample={},
        clock=lambda: datetime(2026, 8, 21, 10, tzinfo=timezone.utc),
    )
    assert record["stage"] == "ready"
    with pytest.raises(ValueError, match="already ready"):
        store.save(
            node_id="ave", avatar=avatar, text="Other", practice=["sound"], sample={},
            clock=lambda: datetime(2026, 8, 21, 11, tzinfo=timezone.utc),
        )
