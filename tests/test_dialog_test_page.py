from streamlit.testing.v1 import AppTest


def test_dialog_test_page_exercises_direct_and_query_paths() -> None:
    app = AppTest.from_file("pages/99_Dialog_Test.py").run(timeout=20)
    assert not app.exception
    assert [title.value for title in app.title] == ["DIALOG TEST"]
    assert {
        "OPEN NODE DIALOG",
        "OPEN CONNECTION DIALOG",
        "OPEN STATE DIALOG",
        "OPEN START HERE",
    } <= {button.label for button in app.button}

    next(button for button in app.button if button.label == "OPEN CONNECTION DIALOG").click().run(timeout=20)
    assert not app.exception
    assert any("KUMIORI ↔ Ave" in header.value for header in app.header)
    assert app.session_state["dialog_test_last_trigger"] == "button:connection"

    app = AppTest.from_file("pages/99_Dialog_Test.py")
    app.query_params["dialog_test"] = "state"
    app.run(timeout=20)
    assert not app.exception
    assert any("STATE OF THE ART" in header.value for header in app.header)
    assert app.session_state["dialog_test_last_trigger"] == "query:state"
