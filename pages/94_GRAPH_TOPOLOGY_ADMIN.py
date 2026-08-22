"""Explicit live admin surface for adding player nodes and graph relations."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit

import streamlit as st

from takeover.inhabited_nodes import NODE_STAGES
from takeover.graph_3d import build_graph_3d_figure
from takeover.events import record_event
from takeover.models import Relation, STAGES
from takeover.node_population import PlayerPopulation, make_person_id
from takeover.notion import NotionRegistry
from takeover.player_invitations import (
    create_open_invitation,
    invite_entry_url,
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
    st.caption("AN INVITATION RECORDS AN OPEN DOOR. IT DOES NOT CREATE A PLAYER OR GRANT EDIT RIGHTS.")

st.header("CREATE INVITATION")
st.write(
    "Create an open invitation without naming or pre-creating its future player. "
    "Identity and ownership capability are created only if somebody enters."
)
st.info(
    "INVITATION URL CONTRACT · SEND ?i=CODE. RESERVE ?c=SECRET FOR AN EXISTING PLAYER CAPABILITY."
)
st.text_area(
    "INVITATION MESSAGE TEMPLATE",
    value=(
        "TAKE OVER / OPEN INVITATION\n\n"
        "[INVITER] OPENED THIS DOOR FOR YOU · [CODE]\n\n"
        "Enter through START HERE:\n\n"
        "[GENERATED WEBSITE URL/?i=CODE]\n\n"
        "The invitation records how you arrived. You create your own identity only if you enter."
    ),
    height=250,
    disabled=True,
)
with st.form("topology-create-invitation"):
    invite_note = st.text_area("OPTIONAL NOTE")
    invite_entry_hint = st.selectbox(
        "OPTIONAL ENTRY HINT",
        ("open", "performance", "sound", "artist", "technical"),
    )
    st.markdown(
        f"**INVITED BY** · {player_names.get(invite_inviter_id, 'NOT SELECTED')}  \n"
        "**MODE** · SINGLE USE · **PROJECT STAGE** · APPLICATION"
    )
    invite_confirm = st.checkbox("I UNDERSTAND THIS CREATES A LIVE OPEN INVITATION")
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
        "CREATE INVITE",
        type="primary",
        width="stretch",
        disabled=bool(invite_infrastructure_blockers),
    )

if create_invitation:
    try:
        if not invite_confirm:
            raise ValueError("Confirm the live invitation write.")
        result = create_open_invitation(
            store,
            invited_by=invite_inviter_id,
            inviter_name=player_names.get(invite_inviter_id, invite_inviter_id),
            website_url=invite_website_url,
            note=invite_note,
            entry_hint=invite_entry_hint,
            clock=lambda: datetime.now().astimezone(),
        )
        st.session_state["topology-invitation-result"] = {
            "message": result.message,
            "code": result.invitation.code,
            "url": result.url,
            "invitation": result.invitation,
        }
        record_event(
            st.session_state, "event_invite_generated",
            result.invitation.code, result.invitation.invited_by,
        )
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
            "THIS CODE RECORDS PROVENANCE ONLY. IT DOES NOT IDENTIFY A PLAYER OR GRANT EDIT RIGHTS."
        )
        with st.expander("INVITATION WRITE RESULT"):
            st.json(invitation_result["invitation"])

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
st.header("CURRENT GRAPH / TABLES")
st.subheader("INVITATIONS")
try:
    invitations = store.list_invitations() if store else []
except Exception as exc:
    invitations = []
    st.error(f"INVITATION READ FAILED · {type(exc).__name__}: {exc}")
st.dataframe([
    {
        "code": invitation.code,
        "invited_by": player_names.get(invitation.invited_by, invitation.invited_by),
        "status": invitation.status,
        "created_at": invitation.created_at.isoformat(),
        "entry_hint": invitation.entry_hint,
        "note": invitation.note,
        "consumed_by": invitation.consumed_by,
        "invite_url": (
            invite_entry_url(invite_website_url, code=invitation.code)
            if invite_website_url.strip() else ""
        ),
    }
    for invitation in invitations
], hide_index=True, width="stretch")

st.subheader("PLAYER CAPABILITIES")
st.caption(
    "CAPABILITIES AUTHORISE EXISTING PLAYERS. ONLY VERIFIER STATUS IS STORED; "
    "RAW ?c= SECRETS CANNOT BE RECOVERED FROM NOTION."
)
player_table = []
for row in existing_players:
    metadata = dict(row.get("metadata") or {})
    capability = dict(metadata.get("capability") or {})
    player_table.append({
        "name": row.get("name", ""),
        "person_id": row.get("player_id", ""),
        "node_stage": metadata.get("node_stage", ""),
        "project_stage": row.get("project_stage", ""),
        "status": row.get("status", ""),
        "network_state": row.get("network_state", ""),
        "visibility": row.get("visibility", ""),
        "practice": row.get("practice", ""),
        "capability_status": capability.get("status", "none"),
        "capability_issued_at": capability.get("issued_at", ""),
    })
st.dataframe(player_table, hide_index=True, width="stretch")

st.subheader("RELATIONS")
try:
    graph_entities = store.list_entities() if store else []
    graph_relations = store.list_relations() if store else []
except Exception as exc:
    graph_entities, graph_relations = [], []
    st.error(f"GRAPH READ FAILED · {type(exc).__name__}: {exc}")
st.dataframe([
    {
        "source": relation.source,
        "relation": relation.type,
        "target": relation.target,
        "stage": relation.stage,
        "status": relation.status,
    }
    for relation in graph_relations
], hide_index=True, width="stretch")

st.subheader("INVITATION PROCEDURE")
st.markdown(
    "1. Select **INVITED BY** and the invitation defaults in the sidebar.  \n"
    "2. Add an optional note or entry hint; no friend name is required.  \n"
    "3. Confirm the live write, then press **CREATE INVITE** once.  \n"
    "4. Copy and send the generated **?i=CODE** URL.  \n"
    "5. The invitee enters through START HERE and creates their own player.  \n"
    "6. At persistence, the app creates their Person ID and **?c= ownership capability**, "
    "writes the invited relation, and consumes this invitation."
)

st.divider()
st.header("NOTION GRAPH / 3D")
st.caption(f"{len(graph_entities)} NODES · {len(graph_relations)} RELATIONS · GENERATED POSITION · READ ONLY")
st.plotly_chart(
    build_graph_3d_figure(graph_entities, graph_relations),
    width="stretch", theme=None, config={"displayModeBar": False, "scrollZoom": True},
)
