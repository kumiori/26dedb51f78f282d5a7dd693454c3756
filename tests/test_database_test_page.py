from streamlit.testing.v1 import AppTest


def test_database_test_page_reports_safe_read_only_session_status() -> None:
    app = AppTest.from_file("pages/93_DATABASE_TEST.py")
    app.secrets = {}
    app.run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["DATABASE TEST"]
    corpus = " ".join(
        [*(item.value for item in app.markdown), *(item.value for item in app.caption)]
    )
    assert "READ ONLY" in corpus
    assert "PROVISIONAL" in corpus
    assert "EMPTY" in corpus
    assert {metric.label for metric in app.metric} == {"NODES", "RELATIONS"}
    assert any("FACTORY HEALTH" in item.value for item in app.header)
    assert any("EVENT LOG" in item.value for item in app.subheader)
