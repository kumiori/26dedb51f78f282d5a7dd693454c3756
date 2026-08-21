from pathlib import Path

from takeover.timeline import build_histropedia_html, build_time_mapping_figure, build_time_mapping_rows, build_timeline_figure, histropedia_articles, load_trajectory


ROOT = Path(__file__).resolve().parents[1]


def test_attached_trajectory_is_renderable() -> None:
    payload = load_trajectory(ROOT / "config" / "takeover_trajectory.yaml")
    figure = build_timeline_figure(payload)
    assert payload["schema_version"] == "trajectory-plan/v2"
    assert len(figure.data) == len(payload["primitives"]) + 1


def test_linear_to_nonlinear_mapping_exposes_identity_map_and_residuals() -> None:
    payload = load_trajectory(ROOT / "config" / "takeover_trajectory.yaml")
    figure = build_time_mapping_figure(payload)

    assert [trace.name for trace in figure.data] == ["IDENTITY · q=u", "TENTATIVE MAP · q=f(u)"]
    assert figure.layout.xaxis.title.text == "u = (date − start) / horizon"
    assert figure.layout.yaxis.title.text == "q = qualitative position"
    assert all(left <= right for left, right in zip(figure.data[1].x, figure.data[1].x[1:]))


def test_time_mapping_dataset_exposes_source_and_derived_values() -> None:
    payload = load_trajectory(ROOT / "config" / "takeover_trajectory.yaml")
    rows = build_time_mapping_rows(payload)

    assert len(rows) == len(payload["primitives"])
    assert {"date", "title", "type", "linear", "nonlinear", "residual", "visibility"} <= rows[0].keys()
    assert all(row["residual"] == row["nonlinear"] - row["linear"] for row in rows)


def test_histropedia_uses_every_dated_yaml_primitive() -> None:
    payload = load_trajectory(ROOT / "config" / "takeover_trajectory.yaml")
    articles = histropedia_articles(payload)
    assert len(articles) == len(payload["primitives"])
    assert {article["id"] for article in articles} == {event["id"] for event in payload["primitives"]}
    assert all({"year", "month", "day"} == set(article["from"]) for article in articles)
    rendered = build_histropedia_html(payload, "window.Histropedia={Timeline:function(){this.load=()=>{}}}")
    assert 'id="histropedia-timeline"' in rendered
    assert '"font": "normal 11px Courier New, monospace"' in rendered
    assert "timeline.load(articles)" in rendered
