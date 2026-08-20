"""Isolated test surface for the original static TAKE OVER timeline."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from takeover.timeline import build_timeline_figure, load_trajectory


ROOT = Path(__file__).resolve().parents[1]
TRAJECTORY = ROOT / "config" / "takeover_trajectory.yaml"

st.set_page_config(page_title="TAKE OVER · Static timeline test", page_icon="+", layout="wide")

st.title("STATIC TIMELINE / TEST")
st.caption("ORIGINAL PLOTLY RENDERER · READ-ONLY · YAML SOURCE")

trajectory = load_trajectory(TRAJECTORY)
st.plotly_chart(
    build_timeline_figure(trajectory),
    width="stretch",
    theme=None,
    config={"displayModeBar": False, "scrollZoom": False},
)

st.caption("SOURCE · config/takeover_trajectory.yaml · trajectory-plan/v2")
