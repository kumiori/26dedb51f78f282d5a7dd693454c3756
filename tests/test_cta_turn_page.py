from streamlit.testing.v1 import AppTest


def test_cta_turn_page_exposes_adjustable_reference_geometry() -> None:
    app = AppTest.from_file("pages/98_CTA_TURN_TEST.py").run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["CTA / TURN TEST"]
    assert {slider.label for slider in app.slider} == {
        "TURN / DEGREES",
        "CORNER CUT / PERCENT",
    }
    corpus = " ".join(item.value for item in app.markdown)
    assert 'class="cta-turn-action"' in corpus
    assert "clip-path:polygon" in corpus
    assert "OPEN APPLICATION FILE" in corpus
    assert "APPLICATION-TAKEOVER%E2%80%A2kumiori-ALB.pdf" in corpus
    assert 'target="_blank"' in corpus
