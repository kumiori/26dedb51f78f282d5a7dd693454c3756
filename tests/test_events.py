from takeover.events import list_events, record_event, record_event_once


def test_event_stream_keeps_every_event_and_deduplicates_only_explicit_tokens() -> None:
    state = {}
    record_event(state, "event_navigate", "voices")
    record_event(state, "event_navigate", "resources")
    assert record_event_once(state, "session", "event_session_started") is True
    assert record_event_once(state, "session", "event_session_started") is False

    events = list_events(state)
    assert [event["target"] for event in events[:2]] == ["voices", "resources"]
    assert [event["label_key"] for event in events].count("event_session_started") == 1
    assert all(event["occurred_at"].endswith("+00:00") for event in events)
