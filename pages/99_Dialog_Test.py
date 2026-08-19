"""Isolated RC0 dialog and iframe-navigation diagnostic surface."""

from __future__ import annotations

import html

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="TAKE OVER · Dialog Test", page_icon="+", layout="wide")


@st.dialog("NODE · TEST")
def node_test() -> None:
    st.caption("NODE DIALOG OPENED")
    st.header("Ave")
    st.write("artist · application")
    st.code("dialog_test=node")


@st.dialog("CONNECTION · TEST")
def connection_test() -> None:
    st.caption("CONNECTION DIALOG OPENED")
    st.header("KUMIORI ↔ Ave")
    st.write("ACTIVE RELATION · COLLABORATES_WITH")
    st.code("dialog_test=connection")


@st.dialog("STATE OF THE ART · TEST", width="large")
def state_test() -> None:
    st.caption("NETWORK-STATE DIALOG OPENED")
    st.header("STATE OF THE ART")
    st.write("3 nodes · 3 connections · 1.33 connectivity · 3 contributions active")
    st.code("dialog_test=state")


@st.dialog("START HERE · TEST")
def start_test() -> None:
    st.caption("START-HERE DIALOG OPENED")
    st.header("START HERE")
    st.write("The central activation door responded.")
    st.code("dialog_test=start")


DIALOGS = {
    "node": node_test,
    "connection": connection_test,
    "state": state_test,
    "start": start_test,
}


st.title("DIALOG TEST")
st.caption("ISOLATED DIAGNOSTIC · NO REGISTRY WRITES · NO PUBLIC NODE CREATION")
st.write(
    "Use the direct buttons first. Then use the framed links. If buttons work but "
    "framed links do not, the failure is in iframe navigation rather than Streamlit dialogs."
)

st.subheader("1 · DIRECT BUTTONS")
columns = st.columns(4)
for column, (key, label) in zip(
    columns,
    (
        ("node", "OPEN NODE DIALOG"),
        ("connection", "OPEN CONNECTION DIALOG"),
        ("state", "OPEN STATE DIALOG"),
        ("start", "OPEN START HERE"),
    ),
):
    with column:
        if st.button(label, key=f"direct-{key}", use_container_width=True):
            st.session_state["dialog_test_last_trigger"] = f"button:{key}"
            DIALOGS[key]()

st.subheader("2 · GRAPH-LIKE FRAMED LINKS")
st.caption("These links cross the same iframe → top-page boundary used by the network graph.")
links = "".join(
    f'<a href="?dialog_test={html.escape(key)}" target="_top">{html.escape(label)}</a>'
    for key, label in (
        ("node", "NODE ↗"),
        ("connection", "CONNECTION ↗"),
        ("state", "STATE OF THE ART ↗"),
        ("start", "START HERE ↗"),
    )
)
components.html(
    f"""
    <style>
      body {{ margin:0; font-family:'Courier New',monospace; }}
      nav {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }}
      a {{ padding:18px 12px; border:1px solid #111; color:#111; text-align:center;
           text-decoration:none; font-size:12px; letter-spacing:.08em; }}
      a:hover,a:focus {{ background:#111; color:#fff; }}
    </style>
    <nav>{links}</nav>
    """,
    height=72,
    scrolling=False,
)

requested = str(st.query_params.get("dialog_test", "") or "").strip().lower()
if requested in DIALOGS:
    token = f"query:{requested}"
    st.session_state["dialog_test_last_trigger"] = token
    DIALOGS[requested]()

st.subheader("3 · OBSERVED STATE")
st.json(
    {
        "query_parameter": requested or None,
        "last_trigger": st.session_state.get("dialog_test_last_trigger"),
        "expected_dialog": requested if requested in DIALOGS else None,
    }
)
st.caption("Return to the main app after recording which trigger did or did not open.")
