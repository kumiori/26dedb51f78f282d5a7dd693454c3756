"""Isolated test surface for the dynamic TAKE OVER timeline."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from takeover.timeline import build_histropedia_html, load_trajectory


ROOT = Path(__file__).resolve().parents[1]
TRAJECTORY = ROOT / "config" / "takeover_trajectory.yaml"
HISTROPEDIA = ROOT / "assets" / "vendor" / "histropedia.umd.min.js"

st.set_page_config(page_title="TAKE OVER · Dynamic timeline test", page_icon="+", layout="wide")

st.title("DYNAMIC TIMELINE / TEST")
st.caption("HISTROPEDIAJS 1.5.0 · INTERACTIVE TEST · READ-ONLY · YAML SOURCE")

trajectory = load_trajectory(TRAJECTORY)
components.html(
    build_histropedia_html(trajectory, HISTROPEDIA.read_text(encoding="utf-8")),
    height=650,
    scrolling=False,
)

st.caption("SOURCE · config/takeover_trajectory.yaml · trajectory-plan/v2")
