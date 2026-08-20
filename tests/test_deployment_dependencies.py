from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_deployment_installs_application_extra() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    active = [line.strip() for line in requirements if line.strip() and not line.startswith("#")]
    assert active == [".[app]"]

    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    assert "PyYAML==6.0.3" in project["optional-dependencies"]["app"]
