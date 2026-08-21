from streamlit.testing.v1 import AppTest


def test_authentication_test_page_generates_a_visible_emoji_projection() -> None:
    app = AppTest.from_file("pages/95_Authentication_Test.py").run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["PERSONA / AUTHENTICATION TEST"]
    next(button for button in app.button if button.label == "GENERATE PERSONA").click().run(timeout=20)

    assert not app.exception
    corpus = " ".join(block.value for block in app.markdown)
    assert "YOUR EMOJI PROJECTION" in corpus
    assert "PROVISIONAL · SESSION-LOCAL" in corpus
    assert len(app.session_state["takeover_personas"]) == 1
    assert app.session_state["takeover_persona_interactions"][0]["kind"] == "persona_minted"
