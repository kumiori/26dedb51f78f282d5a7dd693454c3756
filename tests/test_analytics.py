import sys
from types import SimpleNamespace

from takeover.analytics import emit_google_event, normalise_activation, valid_measurement_id


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
