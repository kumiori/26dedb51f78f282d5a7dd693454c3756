from datetime import date
from pathlib import Path

from takeover.resources import application_date, build_resources_figure, load_resources
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
        "ALLOCATED RESOURCES", "INVESTMENT INTENTION · δ", "INTENTION"
    ]
    assert list(figure.data[0].y) == [0.0, 0.0, 0.0]
    assert list(figure.data[1].y) == [0.0, 1.0, None]
    assert list(figure.data[2].customdata[0]) == ["D−1", "intention", "€0 ALLOCATED"]
    assert figure.layout.annotations[0].text == "D−2 · INCEPTION: THE MYTH OF THE CAVE"
    assert figure.layout.annotations[1].text.startswith("D−1 · INTENTION")
    assert application_date(trajectory) == date(2027, 3, 10)
    assert max(figure.data[0].x) < min(figure.layout.xaxis.tickvals)
    assert "Mai's text" == figure.layout.xaxis.ticktext[0]
    assert figure.layout.title.text == "Allocated resources (in EUR)"
    assert list(figure.layout.yaxis.tickvals) == [0]
    assert figure.layout.yaxis2.visible is False
