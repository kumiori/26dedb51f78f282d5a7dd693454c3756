from streamlit.testing.v1 import AppTest


def test_static_timeline_test_page_uses_the_original_renderer() -> None:
    app = AppTest.from_file("pages/97_Static_Timeline_Test.py").run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["STATIC TIMELINE / TEST"]
    assert len(app.get("plotly_chart")) == 1
    assert any("ORIGINAL PLOTLY RENDERER" in caption.value for caption in app.caption)
    assert any("trajectory-plan/v2" in caption.value for caption in app.caption)
