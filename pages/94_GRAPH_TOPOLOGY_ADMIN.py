"""Explicit live admin surface for adding player nodes and graph relations."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
import uuid

import streamlit as st

from takeover.inhabited_nodes import NODE_STAGES
from takeover.graph_3d import build_graph_3d_figure
from takeover.events import record_event
from takeover.models import Relation, STAGES
from takeover.node_population import PlayerPopulation, make_person_id
from takeover.notion import NotionRegistry
from takeover.player_invitations import (
    create_player_invitation,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "takeover_notion.json"
NETWORK_STATES = ("active", "latent_known", "latent_private", "unknown")
VISIBILITIES = ("public", "private", "anonymous")
REGISTRY_STATUSES = ("active", "draft", "dormant", "archived")
RELATION_TYPES = ("collaborates_with", "invited_by")


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


def relation_id(source: str, relation_type: str, target: str) -> str:
    raw = f"relation-{source}-{relation_type}-{target}".lower()
    return re.sub(r"[^a-z0-9_-]+", "-", raw).strip("-")


def generate_identity() -> None:
    name = str(st.session_state.get("topology-name") or "").strip()
    if not name:
        return
    person_id, initial_condition = make_person_id(
        name, datetime.now().astimezone().isoformat(timespec="seconds"),
    )
    st.session_state["topology-person-id"] = person_id
    st.session_state["topology-initial-condition"] = initial_condition


def reset_identity() -> None:
    st.session_state.pop("topology-person-id", None)
    st.session_state.pop("topology-initial-condition", None)


def default_app_url() -> str:
    configured = os.getenv("TAKEOVER_APP_URL", "").strip()
    if configured:
        return configured.rstrip("/")
    try:
        current = urlsplit(str(st.context.url or ""))
    except Exception:
        return ""
    if current.scheme in {"http", "https"} and current.netloc:
        return urlunsplit((current.scheme, current.netloc, "", "", ""))
    return ""


st.set_page_config(page_title="TAKE OVER · Graph topology admin", page_icon="!", layout="wide")
st.title("GRAPH TOPOLOGY / ADMIN TEST")
st.warning("LIVE NOTION ADMIN. THIS PAGE ADDS OR UPDATES PLAYERS AND RELATIONS.")

if os.getenv("TAKEOVER_ADMIN_MODE", "").strip() != "1":
    st.error("ADMIN MODE IS DISABLED. SET TAKEOVER_ADMIN_MODE=1 TO USE THIS PAGE.")
    st.stop()

token = notion_token()
if not token:
    st.error("NOTION TOKEN IS NOT CONFIGURED. LIVE OPERATIONS ARE DISABLED.")

store = NotionRegistry(token, MANIFEST) if token else None
try:
    existing_players = store.list_players() if store else []
except Exception as exc:
    existing_players = []
    st.error(f"PLAYER LOOKUP FAILED · {type(exc).__name__}: {exc}")
existing_ids = sorted(row["player_id"] for row in existing_players if row.get("player_id"))
player_names = {
    str(row.get("player_id") or ""): str(row.get("name") or row.get("player_id") or "")
    for row in existing_players
}
default_inviter = next(
    (
        player_id
        for player_id in existing_ids
        if player_id == "kumiori" or player_names.get(player_id, "").strip().lower() == "kumiori"
    ),
    existing_ids[0] if existing_ids else "",
)

with st.sidebar:
    st.header("INVITATION PARAMETERS")
    if store:
        st.success("NOTION / CONNECTED")
    else:
        st.error("NOTION / NOT CONNECTED")
    invite_website_url = st.text_input("INVITATION / WEBSITE URL", value=default_app_url())
    invite_inviter_id = st.selectbox(
        "INVITATION / INVITED BY",
        existing_ids or [""],
        index=(existing_ids.index(default_inviter) if default_inviter in existing_ids else 0),
        format_func=lambda value: player_names.get(value, "NO PLAYER AVAILABLE") if value else "NO PLAYER AVAILABLE",
        disabled=not existing_ids,
    )
    invite_already_collaborating = st.checkbox(
        "INVITATION / ALREADY COLLABORATING",
        value=False,
    )
    invite_label = st.text_input("INVITATION / LABEL", value="Person • Alien")
    invite_project_stage = st.selectbox(
        "INVITATION / PROJECT STAGE",
        STAGES,
        index=STAGES.index("application"),
    )
    invite_node_stage = st.selectbox(
        "INVITATION / NODE STAGE",
        NODE_STAGES,
        index=NODE_STAGES.index("invited"),
    )
    invite_network_state = st.selectbox(
        "INVITATION / NETWORK STATE",
        NETWORK_STATES,
        index=NETWORK_STATES.index("latent_private"),
    )
    invite_visibility = st.selectbox(
        "INVITATION / VISIBILITY",
        VISIBILITIES,
        index=VISIBILITIES.index("public"),
    )
    invite_status = st.selectbox(
        "INVITATION / STATUS",
        REGISTRY_STATUSES,
        index=REGISTRY_STATUSES.index("draft"),
    )
    st.caption("THESE VALUES ARE APPLIED TO THE SIMPLIFIED INVITATION FORM.")

st.header("INVITE A PLAYER")
st.write(
    "Create a quiet, latent node now. The invited person receives one private link, "
    "inhabits the node with a few details, and then sees the next upload instructions."
)
with st.form("topology-invite-player"):
    invite_name = st.text_input("INVITED PLAYER / NAME")
    invite_practice = st.text_input("PRACTICE / OPTIONAL")
    st.markdown(
        f"**INVITED BY** · {player_names.get(invite_inviter_id, 'NOT SELECTED')}  \n"
        f"**DEFAULT STATE** · {invite_node_stage.upper()} · {invite_network_state.upper()} · {invite_visibility.upper()}"
    )
    invite_confirm = st.checkbox("I UNDERSTAND THIS CREATES A LIVE INVITED PLAYER")
    invite_infrastructure_blockers = []
    if not store:
        invite_infrastructure_blockers.append("NOTION CONNECTION")
    if not invite_inviter_id:
        invite_infrastructure_blockers.append("INVITER")
    if not invite_website_url.strip():
        invite_infrastructure_blockers.append("WEBSITE URL")
    if invite_infrastructure_blockers:
        st.warning("INVITATION BLOCKED · REQUIRED: " + " · ".join(invite_infrastructure_blockers))
    create_invitation = st.form_submit_button(
        "CREATE PLAYER + INVITATION",
        type="primary",
        width="stretch",
        disabled=bool(invite_infrastructure_blockers),
    )

if create_invitation:
    try:
        if not invite_name.strip():
            raise ValueError("Invited player name is required.")
        if not invite_confirm:
            raise ValueError("Confirm the live invited-player write.")
        request_id = st.session_state.setdefault(
            "topology-invitation-request-id", uuid.uuid4().hex
        )
        result = create_player_invitation(
            store,
            name=invite_name,
            inviter_id=invite_inviter_id,
            practice=invite_practice,
            website_url=invite_website_url,
            request_id=request_id,
            clock=lambda: datetime.now().astimezone(),
            already_collaborating=invite_already_collaborating,
            label=invite_label,
            project_stage=invite_project_stage,
            node_stage=invite_node_stage,
            status=invite_status,
            network_state=invite_network_state,
            visibility=invite_visibility,
        )
        st.session_state["topology-invitation-result"] = {
            "message": result.message,
            "code": result.code,
            "url": result.url,
            "node": result.player,
            "relations": list(result.relation_readbacks),
        }
        record_event(st.session_state, "event_invite_generated", result.player["player_id"], request_id)
        for relation in result.relations:
            record_event(st.session_state, "event_relation_created", relation.id, relation.type)
        st.session_state["topology-invitation-request-id"] = uuid.uuid4().hex
    except Exception as exc:
        st.session_state["topology-invitation-result"] = {
            "error": f"{type(exc).__name__}: {exc}"
        }

invitation_result = st.session_state.get("topology-invitation-result")
if invitation_result:
    if invitation_result.get("error"):
        st.error(invitation_result["error"])
    else:
        st.success(f"INVITATION READY · CODE {invitation_result['code']}")
        st.text_area(
            "COPY / PASTE INVITATION",
            value=invitation_result["message"],
            height=260,
        )
        st.caption(
            "THE FIVE-CHARACTER CODE HELPS THE PERSON RECOGNISE THE INVITATION. "
            "THE PRIVATE LINK ALSO CARRIES THE UNGUESSABLE, PLAYER-SCOPED WRITE CAPABILITY."
        )
        with st.expander("INVITATION WRITE RESULT"):
            st.json({
                "node": invitation_result["node"],
                "relations": invitation_result["relations"],
            })

st.divider()

st.header("NODE")
name = st.text_input("NAME / INITIAL CANONICAL NAME", key="topology-name")
generate_column, reset_column = st.columns(2)
generate_column.button(
    "GENERATE PERSON ID", on_click=generate_identity,
    disabled=not name.strip(), width="stretch",
)
reset_column.button("RESET GENERATED ID", on_click=reset_identity, width="stretch")
st.session_state.setdefault("topology-person-id", "")
player_id = st.text_input("PERSON ID", key="topology-person-id", disabled=True)
initial_condition = dict(st.session_state.get("topology-initial-condition") or {})
st.markdown("**IMMUTABLE INITIAL CONDITION**")
st.json(initial_condition)
st.caption("THE ID IS GENERATED ONCE. LATER CHANGES TO NAME, BIO, PRACTICE OR SAMPLE DO NOT RECALCULATE IT.")
label = st.text_input("LABEL", placeholder="Person • Alien / practice / application")
project_stage = st.selectbox("PROJECT STAGE", STAGES)
node_stage = st.selectbox("NODE STAGE", NODE_STAGES, index=NODE_STAGES.index("node_population"))
network_state = st.selectbox("NETWORK STATE", NETWORK_STATES)
visibility = st.selectbox("VISIBILITY", VISIBILITIES)
status = st.selectbox("REGISTRY STATUS", REGISTRY_STATUSES)
image_url = st.text_input("AVATAR / IMAGE URL")
bio = st.text_area("BIO")
practice = st.text_input("PRACTICE")
sample_url = st.text_input("SAMPLE URL")
metadata_json = st.text_area("EXTRA METADATA JSON", value="{}")

st.header("TOPOLOGY / RELATIONS")
st.caption("POSITIONS ARE GENERATED BY THE RENDERER. NO X/Y VALUES ARE STORED.")
targets = st.multiselect("CONNECT NEW NODE TO", existing_ids)
relation_type = st.selectbox(
    "RELATION TYPE",
    RELATION_TYPES,
    format_func=lambda value: value.replace("_", " ").upper(),
)
st.caption(
    "DIRECTION · NEW / EDITED PLAYER → "
    f"{relation_type.upper()} → SELECTED PLAYER"
)
relation_status = st.selectbox("RELATION STATUS", REGISTRY_STATUSES, key="topology-relation-status")

confirm = st.checkbox("I UNDERSTAND THIS WRITES TO LIVE TAKEOVER DATABASES")
write_blockers = []
if not store:
    write_blockers.append("NOTION CONNECTION")
if not player_id.strip():
    write_blockers.append("PERSON ID")
if not name.strip():
    write_blockers.append("NAME")
if not confirm:
    write_blockers.append("LIVE-WRITE CONFIRMATION")
if write_blockers:
    st.warning("WRITE BLOCKED · REQUIRED: " + " · ".join(write_blockers))
else:
    st.success("WRITE READY · NODE MAY BE UPSERTED")
write = st.button(
    "ADD / UPSERT NODE + RELATIONS", type="primary", width="stretch",
    disabled=bool(write_blockers),
)

if write:
    try:
        metadata = json.loads(metadata_json.strip() or "{}")
        if not isinstance(metadata, dict):
            raise ValueError("Extra metadata must be a JSON object.")
        metadata.pop("node_stage", None)
        metadata.pop("initial_condition", None)
        payload = PlayerPopulation(
            player_id=player_id.strip(), name=name.strip(), label=label.strip(),
            image_url=image_url.strip(), bio=bio.strip(), practice=practice.strip(),
            sample_url=sample_url.strip(), metadata=metadata,
            project_stage=project_stage, node_stage=node_stage, status=status,
            network_state=network_state, visibility=visibility,
            initial_condition=initial_condition,
        )
        node_result = store.upsert_player(payload)
        relation_results = [
            store.upsert_player_relation(Relation(
                relation_id(payload.player_id, relation_type.strip(), target),
                payload.player_id, target, relation_type.strip(), project_stage, relation_status,
            ))
            for target in targets
        ]
        st.session_state["topology-admin-result"] = {
            "node": node_result, "relations": relation_results,
        }
    except Exception as exc:
        st.session_state["topology-admin-result"] = {
            "error": f"{type(exc).__name__}: {exc}",
        }

result = st.session_state.get("topology-admin-result")
if result:
    st.divider()
    st.header("WRITE + READ-BACK")
    if result.get("error"):
        st.error(result["error"])
    else:
        st.success("NODE AND RELATIONS PERSISTED")
        st.subheader("NODE")
        st.json(result["node"])
        st.subheader("RELATIONS")
        st.json(result["relations"])
        st.metric("RELATIONS WRITTEN", len(result["relations"]))

st.divider()
st.header("NOTION GRAPH / 3D")
try:
    graph_entities = store.list_entities() if store else []
    graph_relations = store.list_relations() if store else []
except Exception as exc:
    graph_entities, graph_relations = [], []
    st.error(f"GRAPH READ FAILED · {type(exc).__name__}: {exc}")
st.caption(f"{len(graph_entities)} NODES · {len(graph_relations)} RELATIONS · GENERATED POSITION · READ ONLY")
st.plotly_chart(
    build_graph_3d_figure(graph_entities, graph_relations),
    width="stretch", theme=None, config={"displayModeBar": False, "scrollZoom": True},
)
