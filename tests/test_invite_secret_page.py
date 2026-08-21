from streamlit.testing.v1 import AppTest


def test_invite_generator_page_renders_without_exposing_values_initially() -> None:
    app = AppTest.from_file("pages/96_Invite_Secret_Generator.py").run(timeout=20)
    assert not app.exception
    assert [title.value for title in app.title] == ["INVITE SECRET GENERATOR"]
    assert app.button[0].disabled
    assert app.button[1].disabled
    assert not app.checkbox
    assert all("SAVE" not in button.label and "APPEND" not in button.label for button in app.button)


def test_invite_generator_shows_drop_and_profile_capability_routes() -> None:
    app = AppTest.from_file("pages/96_Invite_Secret_Generator.py").run(timeout=20)
    app.text_input[0].set_value("Viktoria")
    app.button[0].click().run(timeout=20)

    assert not app.exception
    code = [block.value for block in app.code]
    assert any("drop_token" in value and "capability" in value for value in code)
    assert any("?view=resources&k=" in value for value in code)
    assert any("?c=" in value for value in code)
    assert not app.checkbox
    assert all("SAVE" not in button.label and "APPEND" not in button.label for button in app.button)
