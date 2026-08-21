"""Explicit live diagnostic for the production Takeover_Players persistence path."""

from __future__ import annotations

import json
import os
from pathlib import Path
from time import perf_counter

import streamlit as st

from takeover.node_population import PlayerPopulation, load_population_registry, upsert_player_verified
from takeover.notion import NotionRegistry
from takeover.registry import PRESEED_ENTITIES, SEED_ENTITIES


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "takeover_notion.json"
POPULATION = load_population_registry(ROOT / "config" / "takeover_node_population.yaml")
NAMES = {entity.id: entity.title for entity in (*SEED_ENTITIES, *PRESEED_ENTITIES)}
PLAYER_IDS = [str(row["node_id"]) for row in POPULATION["participants"]]


def notion_token() -> str:
    token = os.getenv("NOTION_TOKEN", "").strip()
    if token:
        return token
    try:
        token = str(st.secrets.get("NOTION_TOKEN", "") or "").strip()
        notion = st.secrets.get("notion") or {}
        return token or str(notion.get("token") or notion.get("api_key") or "").strip()
    except Exception:
        return ""


def build_payload() -> PlayerPopulation:
    raw_metadata = st.session_state["player-test-metadata"].strip() or "{}"
    metadata = json.loads(raw_metadata)
    if not isinstance(metadata, dict):
        raise ValueError("Metadata JSON must be an object.")
    metadata.pop("node_stage", None)
    return PlayerPopulation(
        player_id=st.session_state["player-test-id"],
        name=NAMES.get(st.session_state["player-test-id"], st.session_state["player-test-id"]),
        image_url=st.session_state["player-test-image"].strip(),
        bio=st.session_state["player-test-bio"].strip(),
        practice=st.session_state["player-test-practice"].strip(),
        sample_url=st.session_state["player-test-sample"].strip(),
        metadata=metadata,
        project_stage="application",
        node_stage="node_population",
        status=st.session_state["player-test-status"],
    )


def verify(payload: PlayerPopulation, row: dict) -> tuple[bool, list[str]]:
    checks = {
        "Person ID": row.get("player_id") == payload.player_id,
        "Image URL": row.get("image_url") == payload.image_url,
        "Bio": row.get("bio") == payload.bio,
        "Practice": row.get("practice") == payload.practice,
        "Sample URL": row.get("sample_url") == payload.sample_url,
        "Project Stage": row.get("project_stage") == payload.project_stage,
        "Status": row.get("status") == payload.status,
        "Metadata JSON.node_stage": (row.get("metadata") or {}).get("node_stage") == payload.node_stage,
        "Exactly one row": row.get("row_count") == 1,
    }
    return all(checks.values()), [name for name, passed in checks.items() if not passed]


st.set_page_config(page_title="TAKE OVER · Player persistence test", page_icon="!", layout="wide")
st.title("PLAYER PERSISTENCE TEST")
st.warning("LIVE NOTION DIAGNOSTIC. WRITE BUTTONS MODIFY TAKEOVER_PLAYERS.")

selected = st.selectbox("TARGET PLAYER", PLAYER_IDS, key="player-test-id")
st.text_input("PERSON ID", value=selected, disabled=True)
st.text_input("PROJECT STAGE", value="application", disabled=True)
st.text_input("NODE STAGE", value="node_population", disabled=True)
st.text_input("AVATAR / IMAGE URL", key="player-test-image")
st.text_area("BIO", key="player-test-bio")
st.text_input("PRACTICE", key="player-test-practice")
st.text_input("SAMPLE URL", key="player-test-sample")
st.text_area("METADATA JSON", value='{"node_stage": "node_population"}', key="player-test-metadata")
st.selectbox("STATUS", ("active", "draft", "dormant", "archived"), key="player-test-status")

token = notion_token()
if not token:
    st.error("NOTION TOKEN IS NOT CONFIGURED. READ AND WRITE OPERATIONS ARE DISABLED.")

read_column, write_column, repeat_column = st.columns(3)
read_clicked = read_column.button("READ ONLY", disabled=not token, width="stretch")
write_clicked = write_column.button("WRITE / UPSERT", disabled=not token, type="primary", width="stretch")
repeat_clicked = repeat_column.button("REPEAT SAME WRITE", disabled=not token, width="stretch")

if read_clicked or write_clicked or repeat_clicked:
    started = perf_counter()
    try:
        store = NotionRegistry(token, MANIFEST)
        if read_clicked:
            result = store.read_player(selected)
            action = "READ ONLY"
            payload = None
            if result is None:
                result = {"player_id": selected, "row_count": 0, "duplicates": 0}
        else:
            payload = build_payload()
            result = upsert_player_verified(store, payload)
            action = str(result["action"])
        elapsed_ms = (perf_counter() - started) * 1000
        passed, failures = (verify(payload, result) if payload else (result["row_count"] <= 1, [] if result["row_count"] <= 1 else ["Duplicate Person ID"]))
        st.session_state["player-persistence-result"] = {
            "action": action, "result": result, "passed": passed,
            "failures": failures, "latency_ms": elapsed_ms,
        }
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        st.session_state["player-persistence-result"] = {
            "action": "FAILED", "result": {"player_id": selected}, "passed": False,
            "failures": [str(exc)], "latency_ms": (perf_counter() - started) * 1000,
        }
    except Exception as exc:
        st.session_state["player-persistence-result"] = {
            "action": "FAILED", "result": {"player_id": selected}, "passed": False,
            "failures": [f"{type(exc).__name__}: {exc}"], "latency_ms": (perf_counter() - started) * 1000,
        }

diagnostic = st.session_state.get("player-persistence-result")
if diagnostic:
    row = diagnostic["result"]
    st.divider()
    st.header("WRITE RESULT")
    st.subheader(diagnostic["action"])
    st.markdown("**READ-BACK**")
    st.json(row)
    st.metric("ROW COUNT FOR PERSON ID", row.get("row_count", 0))
    if diagnostic["passed"]:
        st.success("PASS")
    else:
        st.error("FAIL · " + " · ".join(diagnostic["failures"]))
    st.divider()
    st.header("RAW DIAGNOSTICS")
    st.text(f"NOTION DATABASE\nTakeover_Players\nPERSON ID LOOKUP\n{row.get('player_id', selected)}")
    st.text(f"ACTION\n{diagnostic['action']}\nPAGE ID\n{row.get('page_id', '')}")
    st.text(f"READBACK LATENCY\n{diagnostic['latency_ms']:.1f} ms\nDUPLICATES\n{row.get('duplicates', 0)}")
