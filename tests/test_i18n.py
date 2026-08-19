from takeover.i18n import UTTERANCES, language_status_metrics, record_translation_proposal


def test_language_status_metrics_derive_from_the_registered_corpus() -> None:
    metrics = language_status_metrics()
    total = len(UTTERANCES)

    assert sum(metrics["en"].values()) == total
    assert metrics["en"]["CANONICAL"] == total
    assert metrics["et"]["PROVISIONAL"] == total
    assert metrics["ru"]["PROVISIONAL"] == total
    assert metrics["fr"]["UNTRANSLATED"] == total


def test_translation_proposals_are_review_only_session_state() -> None:
    state = {}
    original = UTTERANCES[0].text("fr")
    item = record_translation_proposal(state, UTTERANCES[0].key, "fr", "  Proposition  ")
    assert item == {"utterance_key": "project_name", "language": "fr", "proposal": "Proposition"}
    assert state["takeover_translation_proposals"] == [item]
    assert UTTERANCES[0].text("fr") == original
