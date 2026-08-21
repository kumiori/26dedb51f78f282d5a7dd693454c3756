from datetime import datetime, timezone

from takeover.onboarding import CONTRIBUTIONS_KEY, EVENTS_KEY, PARTICIPANTS_KEY, persist_entry


def test_entry_upserts_person_but_appends_distinct_contribution_and_event() -> None:
    state = {}
    first = datetime(2026, 8, 21, 10, tzinfo=timezone.utc)
    second = datetime(2026, 8, 21, 11, tzinfo=timezone.utc)

    persist_entry(
        state, participant_id="persona-1", display_name="A", mode="dj",
        contribution={"listening_link": "https://example.test/one"}, occurred_at=first,
    )
    persist_entry(
        state, participant_id="persona-1", display_name="A", mode="visual",
        contribution={"practice": "Wall-scale image"}, occurred_at=second,
    )

    assert len(state[PARTICIPANTS_KEY]) == 1
    assert state[PARTICIPANTS_KEY]["persona-1"]["role"] == "visual"
    assert state[PARTICIPANTS_KEY]["persona-1"]["created_at"] == first.isoformat()
    assert len(state[CONTRIBUTIONS_KEY]) == 2
    assert len(state[EVENTS_KEY]) == 2
    assert state[EVENTS_KEY][1]["actor"] == "persona-1"
    assert state[EVENTS_KEY][1]["payload"]["contribution_id"] == "entry-2"
