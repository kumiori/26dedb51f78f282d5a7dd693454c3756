"""Small gettext boundary for the i18n specimen page."""

from __future__ import annotations

import gettext
from pathlib import Path


LOCALE_DIR = Path(__file__).resolve().parent.parent / "locales"
LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "ru": "Русский",
    "it": "Italiano",
    "et": "Eesti",
    "es": "Español",
    "sv": "Svenska",
    "zh": "中文",
}


def translator(language: str) -> gettext.NullTranslations:
    """Return the requested catalogue, falling back safely to source English."""
    return gettext.translation(
        "takeover",
        localedir=LOCALE_DIR,
        languages=[language],
        fallback=True,
    )
