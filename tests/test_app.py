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


def test_rc0_application_state_and_qr_activation_are_visible(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("TAKEOVER_GA_MEASUREMENT_ID", raising=False)
    app = AppTest.from_file("app.py")
    app.query_params["a"] = "application"
    app.run(timeout=20)

    assert not app.exception
    corpus = " ".join(block.value for block in app.markdown)
    assert "APPLICATION WINDOW / OPEN" in corpus
    assert "D0 · BEFORE SUBMISSION" in corpus
    assert "PARTICIPANTS" in corpus and "UNKNOWN" in corpus
    assert "PRODUCTION BUDGET" in corpus and "NONE SECURED" in corpus
    assert "EXHIBITION / FEASIBILITY" in corpus and "CONDITIONAL" in corpus
    assert "We do not know whether this will happen." in corpus
    activation_events = [
        event for event in app.session_state["takeover_event_log"]
        if event["label_key"] == "event_invitation_activation"
    ]
    assert len(activation_events) == 1
    assert activation_events[0]["target"] == "application"
    assert activation_events[0]["detail"] == "query:a"

    app.run(timeout=20)
    assert sum(
        event["label_key"] == "event_invitation_activation"
        for event in app.session_state["takeover_event_log"]
    ) == 1


def test_any_invitation_source_is_normalised_and_captured(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("TAKEOVER_GA_MEASUREMENT_ID", raising=False)
    app = AppTest.from_file("app.py")
    app.query_params["a"] = "Reviewer QR"
    app.run(timeout=20)

    events = [
        event for event in app.session_state["takeover_event_log"]
        if event["label_key"] == "event_invitation_activation"
    ]
    assert len(events) == 1
    assert events[0]["target"] == "reviewer-qr"
    assert events[0]["detail"] == "query:a"


def test_landing_process_manifesto_and_entry_share_one_three_column_grid(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("TAKEOVER_GA_MEASUREMENT_ID", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)

    grid = next(block.value for block in app.markdown if 'class="takeover-three-blocks"' in block.value)
    assert grid.count("<article") == 3
    assert grid.index('class="takeover-process"') < grid.index('class="takeover-manifesto"')
    assert grid.index('class="takeover-manifesto"') < grid.index('class="takeover-entry"')
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in CSS


def test_network_connections_and_state_portrait_open_dialogues(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py")
    app.query_params["relation"] = "seed-kumiori-ave"
    app.run(timeout=20)

    assert not app.exception
    corpus = " ".join(block.value for block in app.markdown)
    assert "ACTIVE RELATION" in corpus
    assert "KUMIORI ↔ Ave" in " ".join(title.value for title in app.header)
    assert "COLLABORATES_WITH" in corpus
    assert any(
        event["label_key"] == "event_connection_opened"
        for event in app.session_state["takeover_event_log"]
    )

    app = AppTest.from_file("app.py")
    app.query_params["state"] = "art"
    app.run(timeout=20)
    assert not app.exception
    corpus = " ".join(block.value for block in app.markdown)
    assert "NETWORK STATE" in corpus
    assert "4 active people" in corpus
    assert "1 latent known" in corpus
    assert "1 latent private" in corpus
    assert "2 unknown" in corpus
    assert "4 connections" in corpus
    assert "0.62 connectivity" in corpus
    assert "4 active relations" in corpus


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
    assert "FI · UNTRANSLATED" in corpus and "SV · UNTRANSLATED" in corpus
    assert "IMPROVE THIS TRANSLATION" in corpus
    assert {
        "EN · English", "ET · Eesti", "FI · Suomi", "SV · Svenska",
    } <= {button.label for button in app.main.button}
    assert not {
        "FR · Français", "RU · Русский", "IT · Italiano", "ES · Español", "ZH · 中文",
    } & {button.label for button in app.main.button}
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
        language_term(code) for code in ("en", "et", "fi", "sv")
    ]

    next(button for button in app.main.button if button.label == "ET · Eesti").click().run(timeout=20)
    assert not app.exception
    assert any("HÄÄLED" in block.value for block in app.markdown)


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
