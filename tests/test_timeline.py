from pathlib import Path

from takeover.timeline import build_time_mapping_figure, build_time_mapping_rows, build_timeline_figure, load_trajectory


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
