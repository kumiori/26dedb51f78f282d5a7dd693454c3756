from streamlit.testing.v1 import AppTest


def test_m1_initial_state_is_sparse(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("TAKEOVER_ADMIN_MODE", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    assert [title.value for title in app.main.title] == ["TAKE OVER"]
    assert "+\nSTART HERE" in [button.label for button in app.button]
    assert "Add entity" not in [button.label for button in app.button]


def test_sidebar_has_a_visible_navigation_surface(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    assert "TAKE OVER" in [title.value for title in app.sidebar.title]
    assert {"Network", "Timeline", "Necessities", "I18n lab"}.issubset(
        {button.label for button in app.sidebar.button}
    )


def test_core_views_render_without_a_browser(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    app.button[1].click().run(timeout=20)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1

    app = AppTest.from_file("app.py").run(timeout=20)
    app.button[2].click().run(timeout=20)
    assert not app.exception
    assert any("Application material" in block.value for block in app.markdown)


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


def test_i18n_lab_switches_catalogue_and_plural_form(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    next(button for button in app.button if button.label == "I18N LAB").click().run(timeout=20)
    assert not app.exception
    assert any("Many voices." in block.value for block in app.markdown)

    next(button for button in app.button if button.label == "Français").click().run(timeout=20)
    assert not app.exception
    assert any("Plusieurs voix." in block.value for block in app.markdown)
    app.slider[0].set_value(2).run(timeout=20)
    assert any("2 portes ouvertes" in block.value for block in app.markdown)

    next(button for button in app.button if button.label == "Español").click().run(timeout=20)
    assert any("Muchas voces." in block.value for block in app.markdown)
