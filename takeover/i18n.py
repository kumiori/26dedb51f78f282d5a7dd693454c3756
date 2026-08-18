"""Gettext boundary and the public corpus of TAKE OVER utterances."""

from __future__ import annotations

import gettext
from dataclasses import dataclass
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

VOICE_LANGUAGES = ("en", "et", "fr", "it")


@dataclass(frozen=True)
class Utterance:
    message: str
    weight: int
    context: str | None = None
    note: str = ""


# This is deliberately ordered by visual weight, not alphabetically or by file.
# It is also the single inventory used by the read-only VOICES surface.
UTTERANCES = (
    Utterance("TAKE OVER", 100, "project name", '"TAKE OVER" functions both as the project name and an imperative addressed to the visitor.'),
    Utterance("A COMMUNITY IN PROGRESS", 72),
    Utterance("START HERE", 66, "network action"),
    Utterance("Bring your voice, your image, your practice.", 52),
    Utterance("WHAT THE PROJECT NEEDS NOW", 48),
    Utterance("VOICES", 46, "page title"),
    Utterance("TIMELINE", 38, "navigation"),
    Utterance("NECESSITIES", 38, "navigation"),
    Utterance("NETWORK", 38, "navigation"),
    Utterance("YOU?", 34, "network invitation"),
    Utterance("ENTER THE NETWORK", 30),
    Utterance("We start from what remains.", 25),
    Utterance("We open doors.", 25),
    Utterance("We listen. We respond.", 25),
    Utterance("We build what comes next — together.", 25),
    Utterance("This is a live project.", 24),
    Utterance("It grows with every connection.", 24),
    Utterance("APPLICATION", 20, "project stage"),
    Utterance("IN PROGRESS", 20, "necessity status"),
    Utterance("COLLECTING", 20, "necessity status"),
    Utterance("FOUND", 20, "necessity status"),
    Utterance("AGREED", 20, "necessity status"),
    Utterance("OPEN", 20, "necessity status"),
    Utterance("Abstract", 18, "necessity name"),
    Utterance("Material", 18, "necessity name"),
    Utterance("Initial kernel", 18, "necessity name"),
    Utterance("Photographs", 18, "necessity name"),
    Utterance("Voices + sound", 18, "necessity name"),
    Utterance("Translation", 18, "necessity name"),
    Utterance("Open the central node to begin.", 15),
    Utterance("The system grows from explicit relations.", 15),
    Utterance("nothing?", 12, "empty network state"),
    Utterance("IMPROVE THIS TRANSLATION", 12, "translation action"),
    Utterance("Proposals are not open yet.", 10),
)


def translator(language: str) -> gettext.NullTranslations:
    """Return the requested catalogue, falling back safely to source English."""
    return gettext.translation(
        "takeover",
        localedir=LOCALE_DIR,
        languages=[language],
        fallback=True,
    )


def translate(translation: gettext.NullTranslations, message: str, context: str | None = None) -> str:
    """Translate a source utterance, using context where meaning is ambiguous."""
    return translation.pgettext(context, message) if context else translation.gettext(message)
