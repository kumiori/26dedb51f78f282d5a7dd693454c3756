from pathlib import Path

from takeover.timeline import build_timeline_figure, load_trajectory


ROOT = Path(__file__).resolve().parents[1]


def test_attached_trajectory_is_renderable() -> None:
    payload = load_trajectory(ROOT / "config" / "takeover_trajectory.yaml")
    figure = build_timeline_figure(payload)
    assert payload["schema_version"] == "trajectory-plan/v2"
    assert len(figure.data) == len(payload["primitives"]) + 1

