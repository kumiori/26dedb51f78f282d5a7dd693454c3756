from streamlit.testing.v1 import AppTest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_invitation_write_result_serialises_the_record_before_rendering() -> None:
    source = (ROOT / "pages" / "94_GRAPH_TOPOLOGY_ADMIN.py").read_text()

    assert 'st.json(asdict(invitation_result["invitation"]))' in source


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
    assert any("CURRENT GRAPH / TABLES" in item.value for item in app.header)
    assert any("INVITATION PROCEDURE" in item.value for item in app.subheader)
    assert any("INVITATIONS" in item.value for item in app.subheader)
    assert any("PLAYER CAPABILITIES" in item.value for item in app.subheader)
    assert len(app.dataframe) >= 3
    assert {item.label for item in app.selectbox} >= {
        "PROJECT STAGE", "NODE STAGE", "NETWORK STATE", "VISIBILITY",
        "REGISTRY STATUS", "RELATION TYPE", "RELATION STATUS",
        "INVITATION / INVITED BY", "OPTIONAL ENTRY HINT",
    }
    relation_type = next(item for item in app.selectbox if item.label == "RELATION TYPE")
    assert relation_type.options == ["COLLABORATES WITH", "INVITED BY"]
    assert {item.label for item in app.text_input} >= {
        "PERSON ID", "NAME / INITIAL CANONICAL NAME", "LABEL", "AVATAR / IMAGE URL", "PRACTICE", "SAMPLE URL",
        "INVITATION / WEBSITE URL",
    }
    assert {item.label for item in app.text_area} >= {
        "BIO", "EXTRA METADATA JSON", "INVITATION MESSAGE TEMPLATE",
    }
    template = next(
        item for item in app.text_area if item.label == "INVITATION MESSAGE TEMPLATE"
    )
    assert "?i=CODE" in template.value
    assert template.disabled
    assert any(
        "SEND ?i=CODE" in item.value for item in app.info
    )
    assert {item.label for item in app.multiselect} == {"CONNECT NEW NODE TO"}
    assert "ADD / UPSERT NODE + RELATIONS" in {button.label for button in app.button}
    invite_button = next(button for button in app.button if button.label == "CREATE INVITE")
    assert invite_button.disabled
    assert any("Create an open invitation" in item.value for item in app.markdown)
    assert next(
        item for item in app.sidebar.text_input if item.label == "INVITATION / WEBSITE URL"
    ).value == "https://takeover.example"
    blockers = " ".join(item.value for item in app.warning)
    assert "WRITE BLOCKED" in blockers
    assert all(item in blockers for item in ("NOTION CONNECTION", "PERSON ID", "NAME", "LIVE-WRITE CONFIRMATION"))
    assert next(button for button in app.button if button.label == "ADD / UPSERT NODE + RELATIONS").disabled

    next(item for item in app.text_input if item.label == "NAME / INITIAL CANONICAL NAME").input("Ave").run(timeout=20)
    next(button for button in app.button if button.label == "GENERATE PERSON ID").click().run(timeout=20)
    generated = next(item for item in app.text_input if item.label == "PERSON ID").value
    assert generated.startswith("player_") and len(generated) == 23
