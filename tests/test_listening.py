from pathlib import Path

from takeover.listening import load_listening


ROOT = Path(__file__).resolve().parents[1]


def test_suggested_listening_preserves_open_evolving_field() -> None:
    payload = load_listening(ROOT / "config" / "takeover_listening.yaml")
    listening = payload["suggested_listening"]

    assert payload["presentation"]["show_addendum"] is True
    assert listening["status"] == "open"
    assert len(listening["items"]) == 12
    assert len({item["id"] for item in listening["items"]}) == 12
    assert {item["status"] for item in listening["items"]} == {
        "identified",
        "partially_identified",
        "needs_identification",
    }


def test_unresolved_record_is_not_silently_identified() -> None:
    payload = load_listening(ROOT / "config" / "takeover_listening.yaml")
    unresolved = next(
        item for item in payload["suggested_listening"]["items"]
        if item["id"] == "at_real_irreale"
    )

    assert unresolved["status"] == "needs_identification"
    assert "title" not in unresolved and "artist" not in unresolved


def test_newly_identified_records_preserve_release_details() -> None:
    payload = load_listening(ROOT / "config" / "takeover_listening.yaml")
    items = {item["id"]: item for item in payload["suggested_listening"]["items"]}

    metatron = items["dj_metatron_2_the_sky"]
    assert metatron["catalogue_number"] == "Giegling 18"
    assert metatron["year"] == 2016

    mahal = items["glass_beams_mahal"]
    assert mahal["label"] == "Ninja Tune"
    assert mahal["year"] == 2024
    assert mahal["visible_tracks"] == [
        "Horizon",
        "Mahal",
        "Orb",
        "Snake Oil",
        "Black Sand",
    ]
