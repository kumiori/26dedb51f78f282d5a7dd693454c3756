import sys
from types import SimpleNamespace

from takeover.analytics import (
    emit_google_event,
    emit_invitation_events,
    normalise_activation,
    valid_measurement_id,
)


def test_invitation_sources_are_bounded_and_safe() -> None:
    assert normalise_activation(" Reviewer QR ") == "reviewer-qr"
    assert normalise_activation("APPLICATION") == "application"
    assert normalise_activation("!!!") == ""
    assert len(normalise_activation("a" * 100)) == 64


def test_google_analytics_requires_a_measurement_id() -> None:
    assert valid_measurement_id("G-ABC123") is True
    assert valid_measurement_id("UA-123") is False
    assert emit_google_event("", key="test", event_name="test", params={}) is False


def test_google_analytics_uses_the_configured_property(monkeypatch) -> None:
    calls = []
    monkeypatch.setitem(sys.modules, "streamlit_gtag", SimpleNamespace(st_gtag=lambda **kwargs: calls.append(kwargs)))

    emitted = emit_google_event(
        "g-abc123",
        key="invitation-test",
        event_name="invitation_activation",
        params={"activation_source": "application"},
    )

    assert emitted is True
    assert calls == [{
        "key": "invitation-test",
        "id": "G-ABC123",
        "event_name": "invitation_activation",
        "params": {"activation_source": "application"},
    }]


def test_application_invitation_emits_a_distinct_commission_visit(monkeypatch) -> None:
    calls = []
    monkeypatch.setitem(
        sys.modules,
        "streamlit_gtag",
        SimpleNamespace(st_gtag=lambda **kwargs: calls.append(kwargs)),
    )

    emitted = emit_invitation_events("G-ABC123", "application")

    assert emitted == 2
    assert [call["event_name"] for call in calls] == [
        "invitation_activation",
        "commission_application_visit",
    ]
    assert calls[1]["params"] == {
        "event_category": "commission",
        "event_label": "application",
        "activation_source": "application",
        "audience_context": "commission",
        "value": 1,
    }


def test_other_invitations_do_not_emit_a_commission_visit(monkeypatch) -> None:
    calls = []
    monkeypatch.setitem(
        sys.modules,
        "streamlit_gtag",
        SimpleNamespace(st_gtag=lambda **kwargs: calls.append(kwargs)),
    )

    emitted = emit_invitation_events("G-ABC123", "reviewer-qr")

    assert emitted == 1
    assert [call["event_name"] for call in calls] == ["invitation_activation"]
