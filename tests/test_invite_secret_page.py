from streamlit.testing.v1 import AppTest


def test_invite_generator_page_renders_without_exposing_values_initially() -> None:
    app = AppTest.from_file("pages/96_Invite_Secret_Generator.py").run(timeout=20)
    assert not app.exception
    assert [title.value for title in app.title] == ["INVITE SECRET GENERATOR"]
    assert app.button[0].disabled
    assert app.button[1].disabled
