from streamlit.testing.v1 import AppTest


def test_dynamic_timeline_test_page_uses_the_interactive_renderer() -> None:
    app = AppTest.from_file("pages/97_Dynamic_Timeline_Test.py").run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["DYNAMIC TIMELINE / TEST"]
    assert len(app.get("iframe")) == 1
    assert len(app.get("plotly_chart")) == 0
    assert any("INTERACTIVE TEST" in caption.value for caption in app.caption)
    assert any("trajectory-plan/v2" in caption.value for caption in app.caption)
