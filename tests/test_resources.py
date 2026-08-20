from datetime import date
from pathlib import Path

from takeover.resources import application_date, build_bucket_figure, build_combined_resources_figure, build_resources_figure, load_resources
from takeover.timeline import load_trajectory


ROOT = Path(__file__).resolve().parents[1]


def test_resources_overlay_keeps_observations_before_planned_events() -> None:
    trajectory = load_trajectory(ROOT / "config" / "takeover_trajectory.yaml")
    resources = load_resources(ROOT / "config" / "takeover_resources.yaml")
    figure = build_resources_figure(trajectory, resources)

    assert resources["status"] == "observed"
    allocations = resources["allocated_resources"]["observations"]
    assert [item["timing"] for item in allocations] == ["D−2", "D−1", "D0"]
    assert [item["amount_eur"] for item in allocations] == [0, 0, 0]
    assert allocations[0]["label"] == "inception: the myth of the cave"
    assert resources["investment_intentions"][0]["amount_eur"] == 0
    assert [trace.name for trace in figure.data] == [
        "BUCKET OF DOUGH", "INTENTION"
    ]
    assert set(figure.data[0].y) == {0.0}
    assert figure.data[0].line.shape == "spline"
    assert len(figure.data[0].x) == 3 + len(trajectory["primitives"])
    assert list(figure.data[1].y) == [0.0]
    assert list(figure.data[1].customdata[0]) == ["D−1", "intention", "€0 ALLOCATED"]
    assert figure.layout.annotations[0].text == "D−2 · INCEPTION: THE MYTH OF THE CAVE"
    assert figure.layout.annotations[1].text.startswith("D−1 · INTENTION")
    assert all(annotation.showarrow is False for annotation in figure.layout.annotations)
    assert application_date(trajectory) == date(2027, 3, 10)
    assert max(figure.data[0].x[:3]) < min(figure.layout.xaxis.tickvals)
    assert "Mai's text" == figure.layout.xaxis.ticktext[0]
    assert figure.layout.title.text == "Allocated resources (in EUR)"
    assert list(figure.layout.yaxis.tickvals) == [0]
    assert "yaxis2" not in figure.layout


def test_bucket_plot_exposes_volume_and_file_count() -> None:
    figure = build_bucket_figure([
        {"Size": 1024, "LastModified": "2026-08-19T10:00:00+00:00"},
        {"Size": 2048, "LastModified": "2026-08-19T11:00:00+00:00"},
    ])
    assert [trace.name for trace in figure.data] == ["BUCKET OF GOLD"]
    assert figure.data[0].mode == "lines+markers"
    assert figure.data[0].line.shape == "spline"
    assert figure.data[0].line.smoothing == 1.0


def test_combined_plot_uses_calendar_dates_and_one_scaled_axis() -> None:
    trajectory = load_trajectory(ROOT / "config" / "takeover_trajectory.yaml")
    resources = load_resources(ROOT / "config" / "takeover_resources.yaml")
    figure = build_combined_resources_figure(
        trajectory,
        resources,
        [{"Size": 1024, "LastModified": "2026-08-19T10:00:00+00:00"}],
    )
    assert [trace.name for trace in figure.data] == [
        "BUCKET OF DOUGH · €0", "INTENTION", "BUCKET OF GOLD · V̂"
    ]
    assert list(figure.data[1].y) == [0.0]
    assert figure.data[1].marker.symbol == "diamond"
    assert figure.data[1].marker.size == 22
    assert figure.data[-1].yaxis is None
    assert list(figure.data[-1].y)[-1] == 1.0
    assert figure.data[-1].line.shape == "spline"
    assert figure.layout.xaxis.title.text == "CALENDAR DATE"
    assert list(figure.layout.yaxis.ticktext) == ["€0", "V̂ₛ(now)=1"]
    assert "yaxis2" not in figure.layout

    scaled = build_combined_resources_figure(
        trajectory,
        resources,
        [{"Size": 1024, "LastModified": "2026-08-19T10:00:00+00:00"}],
        volume_scale=2.5,
    )
    assert list(scaled.data[-1].y)[-1] == 2.5
    assert list(scaled.layout.yaxis.ticktext)[-1] == "V̂ₛ(now)=2.5"
