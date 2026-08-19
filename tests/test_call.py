from pathlib import Path

from takeover.call import load_call


ROOT = Path(__file__).resolve().parents[1]


def test_call_copy_is_structured_and_collective_responsibility_is_emphasised() -> None:
    call = load_call(ROOT / "config" / "takeover_call.yaml")
    assert len(call["paragraphs"]) == 3
    assert "19 August 2026" in call["paragraphs"][1]
    assert "Vivian Maier" in call["paragraphs"][1]
    assert call["emphasis"] == "PRODUCTION OF THE WORKS IS OUR COLLECTIVE RESPONSIBILITY."
