from streamlit.testing.v1 import AppTest


def test_network_analysis_page_renders_read_only_multiplex_surface() -> None:
    app = AppTest.from_file("pages/92_NETWORK_ANALYSIS_TEST.py")
    app.secrets = {"notion": {"api_key": ""}}
    app.run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "MULTIPLEX NETWORK ANALYSIS / TEST"
    assert {item.value for item in app.subheader} >= {
        "LAYER-SEPARATED 3D PROJECTION", "RELATION LAYERS", "LABELLED RELATIONS",
    }
    assert len(app.get("plotly_chart")) == 2
    assert {metric.label for metric in app.metric} >= {
        "NODES", "RELATIONS", "LAYERS", "DIRECTED DENSITY", "ISOLATES", "WEAK COMPONENTS",
    }
