from datetime import datetime, timezone

from takeover_engine import Entity, Event, Overlay, RegistryState, Relation, apply_overlay, emit_event, remove_overlay


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 20, tzinfo=timezone.utc)


class MemorySink:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def append(self, event: Event) -> Event:
        self.events.append(event)
        return event

    def list(self) -> tuple[Event, ...]:
        return tuple(self.events)


def test_overlay_is_idempotent_and_reversible() -> None:
    source = RegistryState(entities=(Entity("a", "person", "A"),))
    overlay = Overlay("demo", entities=(Entity("a", "person", "Replacement"), Entity("b", "person", "B")), relations=(Relation("r", "a", "b", "knows"),))
    first = apply_overlay(source, overlay)
    second = apply_overlay(first.state, overlay)
    assert [item.id for item in second.state.entities] == ["a", "b"]
    assert remove_overlay(first) == source


def test_event_uses_injected_sink_and_clock() -> None:
    sink = MemorySink()
    event = emit_event(sink, FixedClock(), "opened", event_id="event-1")
    assert event.occurred_at == FixedClock().now()
    assert sink.list() == (event,)
