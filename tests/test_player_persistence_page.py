from streamlit.testing.v1 import AppTest


def test_player_persistence_page_exposes_explicit_production_path_controls(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("pages/97_PLAYER_PERSISTENCE_TEST.py").run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["PLAYER PERSISTENCE TEST"]
    assert {item.label for item in app.selectbox} >= {"TARGET PLAYER", "STATUS"}
    assert {item.label for item in app.text_input} >= {
        "PERSON ID", "PROJECT STAGE", "NODE STAGE", "AVATAR / IMAGE URL", "PRACTICE", "SAMPLE URL",
    }
    assert {item.label for item in app.text_area} >= {"BIO", "METADATA JSON"}
    assert {button.label for button in app.button} == {"READ ONLY", "WRITE / UPSERT", "REPEAT SAME WRITE"}
    assert "kumiori" in app.selectbox[0].options
    assert app.text_input[0].value == "kumiori"
    assert app.text_input[1].value == "application"
    assert app.text_input[2].value == "node_population"
