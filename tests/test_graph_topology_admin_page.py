from streamlit.testing.v1 import AppTest


def test_graph_topology_admin_is_gated(monkeypatch) -> None:
    monkeypatch.delenv("TAKEOVER_ADMIN_MODE", raising=False)
    app = AppTest.from_file("pages/94_GRAPH_TOPOLOGY_ADMIN.py").run(timeout=20)
    assert not app.exception
    assert [title.value for title in app.title] == ["GRAPH TOPOLOGY / ADMIN TEST"]
    assert any("ADMIN MODE IS DISABLED" in item.value for item in app.error)


def test_graph_topology_admin_exposes_node_and_relation_contract(monkeypatch) -> None:
    monkeypatch.setenv("TAKEOVER_ADMIN_MODE", "1")
    monkeypatch.setenv("TAKEOVER_APP_URL", "https://takeover.example")
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    app = AppTest.from_file("pages/94_GRAPH_TOPOLOGY_ADMIN.py")
    app.secrets = {}
    app.run(timeout=20)

    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
    assert any("GENERATED POSITION · READ ONLY" in item.value for item in app.caption)
    assert {item.label for item in app.selectbox} >= {
        "PROJECT STAGE", "NODE STAGE", "NETWORK STATE", "VISIBILITY",
        "REGISTRY STATUS", "RELATION TYPE", "RELATION STATUS",
        "INVITATION / INVITED BY", "INVITATION / PROJECT STAGE",
        "INVITATION / NODE STAGE", "INVITATION / NETWORK STATE",
        "INVITATION / VISIBILITY", "INVITATION / STATUS",
    }
    relation_type = next(item for item in app.selectbox if item.label == "RELATION TYPE")
    assert relation_type.options == ["COLLABORATES WITH", "INVITED BY"]
    assert {item.label for item in app.text_input} >= {
        "PERSON ID", "NAME / INITIAL CANONICAL NAME", "LABEL", "AVATAR / IMAGE URL", "PRACTICE", "SAMPLE URL",
        "INVITED PLAYER / NAME", "PRACTICE / OPTIONAL", "INVITATION / WEBSITE URL", "INVITATION / LABEL",
    }
    assert {item.label for item in app.text_area} >= {"BIO", "EXTRA METADATA JSON"}
    assert {item.label for item in app.multiselect} == {"CONNECT NEW NODE TO"}
    assert "ADD / UPSERT NODE + RELATIONS" in {button.label for button in app.button}
    invite_button = next(button for button in app.button if button.label == "CREATE PLAYER + INVITATION")
    assert invite_button.disabled
    assert any("Create a quiet, latent node now" in item.value for item in app.markdown)
    sidebar_selects = {item.label: item.value for item in app.sidebar.selectbox}
    assert sidebar_selects["INVITATION / PROJECT STAGE"] == "application"
    assert sidebar_selects["INVITATION / NODE STAGE"] == "invited"
    assert sidebar_selects["INVITATION / NETWORK STATE"] == "latent_private"
    assert sidebar_selects["INVITATION / VISIBILITY"] == "public"
    assert sidebar_selects["INVITATION / STATUS"] == "draft"
    assert next(
        item for item in app.sidebar.text_input if item.label == "INVITATION / WEBSITE URL"
    ).value == "https://takeover.example"
    assert next(
        item for item in app.sidebar.text_input if item.label == "INVITATION / LABEL"
    ).value == "Person • Alien"
    blockers = " ".join(item.value for item in app.warning)
    assert "WRITE BLOCKED" in blockers
    assert all(item in blockers for item in ("NOTION CONNECTION", "PERSON ID", "NAME", "LIVE-WRITE CONFIRMATION"))
    assert next(button for button in app.button if button.label == "ADD / UPSERT NODE + RELATIONS").disabled

    next(item for item in app.text_input if item.label == "NAME / INITIAL CANONICAL NAME").input("Ave").run(timeout=20)
    next(button for button in app.button if button.label == "GENERATE PERSON ID").click().run(timeout=20)
    generated = next(item for item in app.text_input if item.label == "PERSON ID").value
    assert generated.startswith("player_") and len(generated) == 23
