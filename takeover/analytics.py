"""Optional Google Analytics emission with no embedded property identifier."""

from __future__ import annotations

import re
from typing import Any


MEASUREMENT_ID_PATTERN = re.compile(r"^G-[A-Z0-9]+$")
ACTIVATION_PATTERN = re.compile(r"[^a-z0-9_-]+")


def normalise_activation(value: str) -> str:
    """Return a bounded, analytics-safe invitation source."""
    return ACTIVATION_PATTERN.sub("-", str(value).strip().lower()).strip("-")[:64]


def valid_measurement_id(value: str) -> bool:
    return bool(MEASUREMENT_ID_PATTERN.fullmatch(str(value).strip().upper()))


def emit_google_event(
    measurement_id: str,
    *,
    key: str,
    event_name: str,
    params: dict[str, Any],
) -> bool:
    """Emit through the sibling-project gtag component when configured."""
    clean_id = str(measurement_id).strip().upper()
    if not valid_measurement_id(clean_id):
        return False
    from streamlit_gtag import st_gtag

    st_gtag(key=key, id=clean_id, event_name=event_name, params=params)
    return True


def emit_invitation_events(measurement_id: str, activation: str) -> int:
    """Emit the generic invitation event and route-specific application signal."""
    emitted = int(emit_google_event(
        measurement_id,
        key=f"takeover-invitation-{activation}",
        event_name="invitation_activation",
        params={
            "event_category": "invitation",
            "event_label": activation,
            "activation_source": activation,
            "value": 1,
        },
    ))
    if activation == "application":
        emitted += int(emit_google_event(
            measurement_id,
            key="takeover-commission-application-visit",
            event_name="commission_application_visit",
            params={
                "event_category": "commission",
                "event_label": "application",
                "activation_source": "application",
                "audience_context": "commission",
                "value": 1,
            },
        ))
    return emitted
