"""Suite-wide isolation from operator-local Streamlit credentials."""

import pytest
from streamlit.runtime.secrets import secrets_singleton


@pytest.fixture(autouse=True)
def isolate_streamlit_secrets(monkeypatch):
    """Tests opt into secrets explicitly; never read the developer's file."""
    monkeypatch.setattr(secrets_singleton, "_secrets", {})
