from streamlit.testing.v1 import AppTest

from takeover.i18n import UTTERANCES, language_term
from takeover.style import CSS


def test_m1_initial_state_is_sparse(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("TAKEOVER_ADMIN_MODE", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    assert [title.value for title in app.main.title] == ["TAKE OVER"]
    assert not any("START HERE" in button.label for button in app.button)
    assert "Add entity" not in [button.label for button in app.button]


def test_tooltips_keep_readable_contrast_and_fit() -> None:
    assert '[data-baseweb="tooltip"]' in CSS
    assert "color:var(--paper)!important" in CSS
    assert "width:max-content!important" in CSS


def test_sidebar_has_a_visible_navigation_surface(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    assert "TAKE OVER" in [title.value for title in app.sidebar.title]
    assert {"PROCESS", "TIMELINE", "NEEDS", "RESOURCES", "VOICES"}.issubset(
        {button.label for button in app.sidebar.button}
    )
    assert not any(button.label.startswith(("EN ", "ET ", "RU ")) for button in app.sidebar.button)
    sidebar_corpus = " ".join(block.value for block in app.sidebar.markdown)
    assert "EVENT LOG" in sidebar_corpus
    assert "SESSION STARTED" in sidebar_corpus

    next(button for button in app.sidebar.button if button.label == "VOICES").click().run(timeout=20)
    sidebar_corpus = " ".join(block.value for block in app.sidebar.markdown)
    assert "NAVIGATED" in sidebar_corpus and "voices" in sidebar_corpus


def test_core_views_render_without_a_browser(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    app.button[1].click().run(timeout=20)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2
    assert any("TENTATIVE LINEAR" in block.value for block in app.markdown)
    assert len(app.main.get("plotly_chart")) == 1
    assert len(app.sidebar.get("plotly_chart")) == 1
    assert len(app.sidebar.dataframe) == 3
    assert any("PHASE: APPLICATION" in block.value for block in app.main.markdown)
    assert not any("TENTATIVE LINEAR" in block.value for block in app.main.markdown)

    app = AppTest.from_file("app.py").run(timeout=20)
    app.button[2].click().run(timeout=20)
    assert not app.exception
    assert any("INITIAL KERNEL" in block.value for block in app.markdown)
    needs_corpus = " ".join(block.value for block in app.markdown)
    assert "TO SUBMIT → DONE" in needs_corpus
    assert "NOT YET ACTIVATED" in needs_corpus

    app = AppTest.from_file("app.py").run(timeout=20)
    next(button for button in app.button if button.label == "RESOURCES").click().run(timeout=20)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
    assert any("OBSERVED INTENTION" in block.value for block in app.caption)
    assert len(app.dataframe) == 3


def test_developer_add_node_flow(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.setenv("TAKEOVER_ADMIN_MODE", "1")
    app = AppTest.from_file("app.py").run(timeout=20)
    app.text_input[0].set_value("Ave")
    app.text_input[1].set_value("ave")
    app.text_input[2].set_value("artist")
    next(button for button in app.button if button.label == "Add entity").click().run(timeout=20)
    assert not app.exception
    assert app.session_state["takeover_entities"][0]["id"] == "ave"
    assert app.session_state["takeover_entities"][0]["stage"] == "application"


def test_voices_exposes_weighted_corpus(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    next(button for button in app.button if button.label == "VOICES").click().run(timeout=20)
    assert not app.exception
    corpus = " ".join(block.value for block in app.markdown)
    assert "Bring your voice, your image, your practice." in corpus
    assert "EN · CANONICAL" in corpus
    assert "ET · PROVISIONAL" in corpus
    assert "RU · PROVISIONAL" in corpus
    assert "FR · UNTRANSLATED" in corpus and "IT · UNTRANSLATED" in corpus
    assert "IMPROVE THIS TRANSLATION" in corpus
    assert {
        "EN · English", "FR · Français", "RU · Русский", "IT · Italiano",
        "ET · Eesti", "ES · Español", "SV · Svenska", "ZH · 中文",
    } <= {button.label for button in app.main.button}
    assert "RECORD YOUR VOICE" in corpus
    assert "VOICES STATISTICS" in corpus
    assert "RECORDINGS COMPLETE" in corpus
    assert "TRANSLATION PROPOSALS" in corpus
    main_corpus = " ".join(block.value for block in app.main.markdown)
    sidebar_corpus = " ".join(block.value for block in app.sidebar.markdown)
    assert 'class="voice-stat"' not in main_corpus
    assert "VOICES STATISTICS" in sidebar_corpus
    assert "LANGUAGE STATUS" in sidebar_corpus
    eligible = [utterance for utterance in UTTERANCES if utterance.weight >= 30]
    assert sum(button.label == "🎙" for button in app.main.button) == len(eligible)
    assert sum(button.label == "+" for button in app.main.button) == len(UTTERANCES)
    assert "ADD TRANSLATION" in corpus

    assert app.multiselect[0].label == "WHAT LANGUAGES DO YOU WANT TO READ?"
    assert app.multiselect[0].options == [
        language_term(code) for code in ("en", "fr", "ru", "it", "et", "es", "sv", "zh")
    ]

    next(button for button in app.main.button if button.label == "RU · Русский").click().run(timeout=20)
    assert not app.exception
    assert any("ГОЛОСА" in block.value for block in app.markdown)


def test_translation_proposal_is_session_local_and_does_not_overwrite_corpus(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    next(button for button in app.button if button.label == "VOICES").click().run(timeout=20)
    next(button for button in app.main.button if button.label == "+").click().run(timeout=20)
    assert not app.exception
    assert app.text_area[0].label == "YOUR VERSION"
    assert any("CURRENT TRANSLATION" in caption.value for caption in app.caption)
    assert UTTERANCES[0].text("fr") == "TAKE OVER"


def test_landing_contains_the_exact_take_over_sequence(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    corpus = " ".join(block.value for block in app.markdown)
    sequence = (
        "Take over the wall.",
        "Take over the oven.",
        "Take over the sound.",
        "Take over the restaurant.",
        "Take over the night.",
        "Take over the web surface.",
    )
    positions = [corpus.index(line) for line in sequence]
    assert positions == sorted(positions)
    process_block = next(block.value for block in app.markdown if 'class="takeover-process"' in block.value)
    assert all(line in process_block for line in sequence)
    landing_action = next(block.value for block in app.markdown if 'class="takeover-entry"' in block.value)
    assert "<strong>TAKEOVER</strong>" in landing_action
    assert "Open the central node." in landing_action
    assert "explicit relations" not in landing_action
    assert "ENTER THE NETWORK" not in landing_action
    call_block = next(block.value for block in app.sidebar.markdown if 'class="sidebar-call"' in block.value)
    assert "Fotografiska’s wider exhibition programme" in call_block
    assert "19 August 2026" in call_block
    assert "PRODUCTION OF THE WORKS IS OUR COLLECTIVE RESPONSIBILITY." in call_block
    assert not any('class="sidebar-call"' in block.value for block in app.main.markdown)
