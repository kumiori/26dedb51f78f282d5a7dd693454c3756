"""TAKE OVER — Milestone 2.0 operating surface."""

from __future__ import annotations

import os
import base64
from pathlib import Path
import re
import html
from datetime import datetime, timezone
import hashlib
import json
import secrets
import uuid

import streamlit as st

from takeover.analytics import emit_google_event, emit_invitation_events, normalise_activation
from takeover.browser_encrypt import encrypted_drop
from takeover.call import load_call
from takeover.database_status import RegistryDiagnostics, inspect_registry
from takeover.graph import build_graph_html
from takeover.events import list_events, record_event, record_event_once
from takeover.encrypted_storage import EncryptedContribution, EncryptedRegistry
from takeover.identity import resolve_drop_token, resolve_identity
from takeover.i18n import LANGUAGES, REGISTRY, UTTERANCES, VOICE_LANGUAGES, language_status_metrics, language_term, record_translation_proposal, translate
from takeover.listening import load_listening
from takeover.models import ENTITY_TYPES, STAGES, Entity, Relation, entity_type_label
from takeover.network_analysis import connectivity_history
from takeover.onboarding import ENTRY_MODES, persist_entry
from takeover.persona_auth import ProvisionalPersonaStore, authenticate_persona, mint_persona
from takeover.player_invitations import (
    InvitationRecord,
    InvitationResolution,
    PlayerResolution,
    create_invitation_credentials,
    resolve_capability,
    resolve_invitation,
)
from takeover.public_media import FilebasePublicMediaStore
from takeover.inhabited_nodes import FileNodeStore, PublicNodeMediaStore, node_stage
from takeover.node_population import PlayerPopulation, load_population_registry, make_person_id, population_state, resolve_population_participant, upsert_inhabited_node, upsert_player_verified
from takeover.registry import SessionRegistry, with_rc0_seeds
from takeover.resource_field import load_resource_field, resource_rows
from takeover.resources import build_combined_resources_figure, load_resources
from takeover.style import CSS
from takeover.timeline import build_time_mapping_figure, build_time_mapping_rows, build_timeline_figure, load_trajectory


ROOT = Path(__file__).resolve().parent
TRAJECTORY = ROOT / "config" / "takeover_trajectory.yaml"
RESOURCES = ROOT / "config" / "takeover_resources.yaml"
RESOURCE_FIELD = ROOT / "config" / "takeover_resource_field.yaml"
CALL = ROOT / "config" / "takeover_call.yaml"
LISTENING = ROOT / "config" / "takeover_listening.yaml"
ENCRYPTED_REGISTRY = Path(os.getenv("TAKEOVER_ENCRYPTED_REGISTRY", ROOT / "data" / "encrypted_storage_v1.json"))
NODE_POPULATION = load_population_registry(ROOT / "config" / "takeover_node_population.yaml")
NODE_REGISTRY = Path(os.getenv("TAKEOVER_NODE_REGISTRY", ROOT / "data" / "inhabited_nodes_v1.json"))
NODE_MEDIA = Path(os.getenv("TAKEOVER_NODE_MEDIA", ROOT / "data" / "inhabited_node_media"))
APPLICATION_FILE_URL = "https://console.filebase.com/object/takeover-fotografiska/APPLICATION-TAKEOVER%E2%80%A2HANDOUT.pdf"
PUBLIC_MEDIA_GATEWAY = "https://useless-azure-newt.myfilebase.com/ipfs"

language = st.session_state.get("takeover_language", "en")
if language not in LANGUAGES:
    language = "en"
def t(key: str) -> str:
    return translate(key, language)

st.set_page_config(page_title=t("project_name"), page_icon="+", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)
session_event_new = record_event_once(st.session_state, "session-started", "event_session_started")

activation = normalise_activation(str(st.query_params.get("a", "") or ""))
current_participant_id = resolve_population_participant(NODE_POPULATION, activation)
activation_event_new = False
if activation:
    activation_event_new = record_event_once(
        st.session_state,
        f"invitation-activation-{activation}",
        "event_invitation_activation",
        activation,
        "query:a",
    )


def _secrets_available() -> bool:
    return any(path.exists() for path in (
        ROOT / ".streamlit" / "secrets.toml",
        Path.home() / ".streamlit" / "secrets.toml",
    ))


def _secret(name: str) -> str:
    if not _secrets_available():
        return ""
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


def _notion_token_value() -> str:
    token = os.getenv("NOTION_TOKEN", "").strip() or _secret("NOTION_TOKEN")
    if token:
        return token
    if not _secrets_available():
        return ""
    try:
        notion = st.secrets.get("notion", {})
        return str(notion.get("token") or notion.get("api_key") or "").strip()
    except Exception:
        return ""


def _analytics_measurement_id() -> str:
    return os.getenv("TAKEOVER_GA_MEASUREMENT_ID", "").strip() or _secret("TAKEOVER_GA_MEASUREMENT_ID")


@st.cache_data(ttl=60, show_spinner=False)
def _bucket_objects() -> tuple[list[dict], str]:
    """Read Filebase accounting metadata without mutating the bucket."""
    if not _secrets_available():
        return [], "STORAGE NOT CONFIGURED"
    try:
        import boto3
        from botocore.config import Config
        from botocore.exceptions import BotoCoreError, ClientError

        cfg = st.secrets["filebase"]
        signature = "s3v4" if cfg.get("signature_version", "v4") == "v4" else cfg["signature_version"]
        client = boto3.client(
            "s3", endpoint_url=cfg["endpoint"],
            aws_access_key_id=cfg["access_key"], aws_secret_access_key=cfg["secret_key"],
            region_name=cfg.get("region", "auto"),
            config=Config(signature_version=signature, connect_timeout=2, read_timeout=2, retries={"max_attempts": 1}),
        )
        response = client.list_objects_v2(Bucket=cfg["bucket"])
        return list(response.get("Contents", [])), ""
    except (KeyError, TypeError):
        return [], "STORAGE NOT CONFIGURED"
    except (BotoCoreError, ClientError, OSError) as exc:
        return [], f"BUCKET UNAVAILABLE · {type(exc).__name__}"


def _drop_storage_context():
    """Resolve private drop configuration only when a drop link is opened."""
    try:
        import boto3
        from botocore.config import Config

        cfg = st.secrets["filebase"]
        identities = {
            name: dict(value) for name, value in st.secrets["takeover_identities"].items()
        }
        signature = "s3v4" if cfg.get("signature_version", "v4") == "v4" else cfg["signature_version"]
        client = boto3.client(
            "s3", endpoint_url=cfg["endpoint"],
            aws_access_key_id=cfg["access_key"], aws_secret_access_key=cfg["secret_key"],
            region_name=cfg.get("region", "auto"),
            config=Config(signature_version=signature, connect_timeout=3, read_timeout=5, retries={"max_attempts": 1}),
        )
        return client, str(cfg["bucket"]), identities, ""
    except (KeyError, TypeError):
        return None, "", {}, "STORAGE IS NOT CONFIGURED"


def _public_avatar_store():
    """Build the public Filebase avatar adapter without exposing credentials."""
    try:
        import boto3
        from botocore.config import Config

        cfg = st.secrets["filebase"]
        signature = "s3v4" if cfg.get("signature_version", "v4") == "v4" else cfg["signature_version"]
        client = boto3.client(
            "s3",
            endpoint_url=cfg["endpoint"],
            aws_access_key_id=cfg["access_key"],
            aws_secret_access_key=cfg["secret_key"],
            region_name=cfg.get("region", "auto"),
            config=Config(signature_version=signature, connect_timeout=3, read_timeout=8, retries={"max_attempts": 1}),
        )
        gateway = str(cfg.get("public_gateway") or PUBLIC_MEDIA_GATEWAY)
        return FilebasePublicMediaStore(client, str(cfg["bucket"]), gateway), ""
    except (KeyError, TypeError, ValueError):
        return None, "PUBLIC AVATAR STORAGE IS NOT CONFIGURED"


@st.dialog("DROP / PRIVATE", width="large")
def resource_drop_dialog(participant: str, identities: dict, s3, bucket: str) -> None:
    from botocore.exceptions import BotoCoreError, ClientError

    st.caption(f"FOR · {participant}")
    st.write("SELECT A FILE. PLAINTEXT STAYS IN THIS BROWSER; ONLY CIPHERTEXT ENTERS THE BUCKET OF GOLD.")
    contribution_id = str(uuid.uuid4())
    namespace = hashlib.sha256(f"takeover-drop:{participant}".encode()).hexdigest()[:16]
    object_key = f"private/{participant}/{namespace}/{contribution_id}.enc"
    try:
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": object_key, "ContentType": "application/octet-stream"},
            ExpiresIn=900,
        )
    except (BotoCoreError, ClientError) as exc:
        st.error(f"DROP COULD NOT BE PREPARED · {type(exc).__name__}")
        return

    result = encrypted_drop(
        data={
            "upload_url": upload_url, "object_key": object_key,
            "contribution_id": contribution_id, "participant": participant,
            "identity_key": identities[participant]["access_key"],
            "content_type": "application/octet-stream",
        },
        default={"uploaded": None},
        key=f"resource-private-drop-{participant}",
        on_uploaded_change=lambda: None,
    )
    if not result.uploaded:
        st.caption("SELECT · ENCRYPT · SEND")
        return

    uploaded = dict(result.uploaded)
    expected_prefix = f"private/{participant}/{namespace}/"
    valid = (
        uploaded.get("contributor_id") == participant
        and str(uploaded.get("key", "")).startswith(expected_prefix)
        and uploaded.get("algorithm") == "AES-256-GCM"
        and uploaded.get("version") == 1
        and all(re.fullmatch(r"[A-Za-z0-9_-]+", str(uploaded.get(field, ""))) for field in ("iv", "salt", "wrap_iv", "wrapped_key"))
    )
    if not valid:
        st.error("DROP METADATA FAILED VALIDATION")
        return
    try:
        meta = s3.head_object(Bucket=bucket, Key=uploaded["key"])
    except (BotoCoreError, ClientError) as exc:
        st.error(f"DROP COULD NOT BE VERIFIED · {type(exc).__name__}")
        return

    cid = meta.get("Metadata", {}).get("cid") or meta.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amz-meta-cid")
    row = EncryptedRegistry(ENCRYPTED_REGISTRY).add(EncryptedContribution(
        id=uploaded["id"], contributor_id=participant,
        created_at=datetime.now(timezone.utc).isoformat(),
        object={
            "cid": cid, "key": uploaded["key"], "filename": uploaded["filename"],
            "encrypted_bytes": int(meta.get("ContentLength", uploaded["encrypted_bytes"])),
            "original_bytes": int(uploaded["original_bytes"]),
            "mime_type": "application/octet-stream",
            "original_mime_type": uploaded["original_mime_type"],
        },
        crypto={
            "algorithm": "AES-256-GCM", "version": 1, "iv": uploaded["iv"],
            "kdf": uploaded["kdf"], "salt": uploaded["salt"], "wrap_iv": uploaded["wrap_iv"],
            "wrapped_key": uploaded["wrapped_key"], "key_reference": uploaded["key_reference"],
        },
    ))
    _bucket_objects.clear()
    st.success("RECEIVED / BUCKET OF GOLD")
    st.write(f"**FILE**  {row.object['filename']}")
    st.write(f"**WEIGHT**  {row.object['encrypted_bytes']:,} bytes")
    st.write(f"**CID**  `{row.object['cid'] or 'CID pending'}`")


def render_resource_drop_link() -> None:
    token = str(st.query_params.get("k", "") or "").strip()
    if not token:
        return
    s3, bucket, identities, error = _drop_storage_context()
    if error:
        st.error(error)
        return
    participant = resolve_drop_token(token, identities)
    if participant is None:
        st.warning("THIS DROP LINK IS NOT ACTIVE")
        return
    resource_drop_dialog(participant, identities, s3, bucket)


measurement_id = _analytics_measurement_id()
if session_event_new:
    emit_google_event(
        measurement_id,
        key="takeover-session-started",
        event_name="takeover_session_started",
        params={"event_category": "takeover", "event_label": "session", "value": 1},
    )
if activation_event_new:
    emit_invitation_events(measurement_id, activation)


@st.cache_resource
def _notion_registry(token: str):
    from takeover.notion import NotionRegistry
    return NotionRegistry(token, ROOT / "config" / "takeover_notion.json")


def registry():
    token = _notion_token_value()
    if token:
        return _notion_registry(token), "notion"
    return SessionRegistry(st.session_state), "session"


def switch_view(view: str) -> None:
    st.session_state["takeover_view"] = view
    record_event(st.session_state, "event_navigate", view)


def select_entry_mode(mode: str) -> None:
    st.session_state["start_here_mode"] = mode
    st.session_state.pop("start_here_draft", None)


def _persist_start_here(
    repo, persona, draft: dict, invitation: InvitationRecord | None = None
) -> None:
    attempt_key = (
        f"start-here-attempt:{persona.access_key}:"
        f"{invitation.code if invitation else 'public'}"
    )
    attempt = dict(st.session_state.get(attempt_key) or {})
    if not attempt:
        occurred_at = datetime.now(timezone.utc)
        participant_id, initial_condition = make_person_id(
            str(draft.get("display_name") or persona.nickname or "Anonymous"),
            occurred_at.isoformat(),
        )
        _recognition_code, raw_capability, verifier = create_invitation_credentials()
        attempt = {
            "occurred_at": occurred_at.isoformat(),
            "participant_id": participant_id,
            "initial_condition": initial_condition,
            "raw_capability": raw_capability,
            "verifier": verifier,
        }
        st.session_state[attempt_key] = attempt
    occurred_at = datetime.fromisoformat(str(attempt["occurred_at"]))
    participant_id = f"participant-{persona.access_key[:12].lower()}"
    display_name = str(draft.get("display_name") or persona.nickname or "Anonymous")
    participant, _contribution, _event = persist_entry(
        st.session_state, participant_id=participant_id, display_name=display_name,
        mode=str(draft["mode"]), contribution=dict(draft["payload"]),
        occurred_at=occurred_at,
    )
    if callable(getattr(repo, "upsert_player", None)):
        participant_id = str(attempt["participant_id"])
        initial_condition = dict(attempt["initial_condition"])
        raw_capability = str(attempt["raw_capability"])
        verifier = str(attempt["verifier"])
        contribution = dict(draft["payload"])
        practice = str(contribution.get("practice") or contribution.get("possibility") or "")
        bio = str(contribution.get("reason") or contribution.get("understand") or "")
        sample_url = str(
            contribution.get("link") or contribution.get("listening_link") or ""
        )
        metadata = {
            "primary_mode": participant["role"],
            "source": "invite" if invitation else "public_entry",
            "capability": {
                "version": 1,
                "algorithm": "sha256",
                "verifier": verifier,
                "status": "active",
                "issued_at": occurred_at.isoformat(),
                "revoked_at": None,
            },
        }
        if invitation:
            metadata["invited_by"] = invitation.invited_by
            metadata["invite_code"] = invitation.code
        player = upsert_player_verified(repo, PlayerPopulation(
            player_id=participant_id,
            name=display_name,
            label=f'Person • Alien / {participant["role"]} / application',
            bio=bio,
            practice=practice,
            sample_url=sample_url,
            metadata=metadata,
            initial_condition=initial_condition,
            project_stage="application",
            node_stage="node_population",
            status="active",
            network_state="active",
            visibility="public",
        ))
        if invitation:
            relation = Relation(
                f"relation-{invitation.invited_by}-invited-{participant_id}",
                invitation.invited_by,
                participant_id,
                "invited",
                "application",
                "active",
                {"provenance": "invitation", "invite_code": invitation.code},
            )
            repo.upsert_player_relation(relation)
            repo.consume_invitation(
                invitation.code, player_id=participant_id, consumed_at=occurred_at
            )
        current_url = str(getattr(st.context, "url", "") or "")
        base_url = current_url.split("?", 1)[0].rstrip("/")
        capability_url = (
            f"{base_url}/?c={raw_capability}" if base_url else f"?c={raw_capability}"
        )
        st.session_state["start_here_ownership"] = {
            "player": player,
            "capability_url": capability_url,
        }
    elif not any(item.id == participant_id for item in repo.list_entities()):
        repo.add_entity(Entity(
            participant_id, "person", display_name,
            f'Person • Alien / {participant["role"]} / entry', source="start_here",
            metadata={"primary_mode": participant["role"], "authority": "provisional"},
        ))
    st.session_state["start_here_persisted"] = participant_id
    record_event(st.session_state, "event_entry_persisted", participant_id, str(draft["mode"]))


@st.dialog(t("start_here"), width="large")
def access_door(repo, invitation: InvitationRecord | None = None) -> None:
    if invitation:
        st.markdown(
            f'<div class="entry-question">{html.escape(invitation.invited_by.upper())} '
            "OPENED THIS DOOR FOR YOU.</div>",
            unsafe_allow_html=True,
        )
        if invitation.entry_hint != "open":
            st.caption(f"ENTRY HINT · {invitation.entry_hint.upper()}")
    st.caption("BROWSING IS OPEN · CONTRIBUTING CREATES IDENTITY")
    st.markdown('<div class="entry-flow">ENTER → CHOOSE → CONTRIBUTE → AUTHENTICATE → PERSIST</div>', unsafe_allow_html=True)
    if st.session_state.get("start_here_persisted"):
        st.success("PRESENCE PERSISTED")
        ownership = dict(st.session_state.get("start_here_ownership") or {})
        if ownership.get("capability_url"):
            st.text_input(
                "SAVE YOUR PRIVATE OWNERSHIP LINK",
                value=str(ownership["capability_url"]),
                disabled=True,
            )
            st.caption("THIS ?c= LINK EDITS YOUR EXISTING PLAYER. KEEP IT PRIVATE.")
        st.caption("PERSON ≠ CONTRIBUTION ≠ EVENT")
        return

    mode = str(st.session_state.get("start_here_mode") or "")
    if not mode:
        st.markdown('<div class="entry-question">HOW ARE YOU ENTERING?</div>', unsafe_allow_html=True)
        for mode_id, label in ENTRY_MODES:
            st.button(label, key=f"entry-mode-{mode_id}", width="stretch", on_click=select_entry_mode, args=(mode_id,))
        return

    mode_label = dict(ENTRY_MODES)[mode]
    st.markdown(f'<div class="entry-selected"><small>PRIMARY MODE</small><strong>{html.escape(mode_label)}</strong></div>', unsafe_allow_html=True)
    if st.button("← CHOOSE ANOTHER WAY", key="entry-mode-reset"):
        st.session_state.pop("start_here_mode", None)
        st.session_state.pop("start_here_draft", None)
        st.rerun()

    draft = st.session_state.get("start_here_draft")
    if draft is None:
        with st.form(f"entry-form-{mode}"):
            payload: dict[str, object] = {}
            display_name = ""
            if mode in {"performance", "music", "dj", "visual", "technical"}:
                display_name = st.text_input("NAME")
            if mode == "performance":
                payload["link"] = st.text_input("ONE LINK", placeholder="Instagram / website / video")
                payload["practice"] = st.text_area("WHAT KIND OF MOVEMENT OR PRACTICE DO YOU BRING?")
            elif mode in {"music", "dj"}:
                payload["listening_link"] = st.text_input("ONE LISTENING LINK")
                payload["practice"] = st.text_area("ONE SENTENCE ON YOUR PRACTICE")
                payload["availability_setup"] = st.text_input("AVAILABILITY / LIVE SETUP · OPTIONAL")
            elif mode == "visual":
                payload["link"] = st.text_input("ONE LINK")
                payload["references"] = st.text_area("1–3 REFERENCE IMAGE LINKS")
                payload["practice"] = st.text_area("ONE SENTENCE ON MEDIUM / SCALE / SURFACE")
            elif mode == "technical":
                payload["possibility"] = st.text_area("WHAT CAN YOU BRING OR MAKE POSSIBLE?")
                payload["capacities"] = st.multiselect(
                    "CAPACITIES", ("equipment", "fabrication", "projection", "sound", "lighting", "rigging", "coding", "brainstorming", "thinking", "other"),
                )
                payload["references"] = st.text_area("FILES / SPECS / PHOTO LINKS · OPTIONAL")
            elif mode == "commission":
                payload["understand"] = st.text_area("WHAT WOULD YOU WANT TO UNDERSTAND BETTER?")
                payload["unresolved"] = st.text_area("WHAT FEELS UNRESOLVED?")
                payload["curiosity"] = st.text_area("WHAT WOULD MAKE YOU CURIOUS ENOUGH TO CONTINUE?")
                payload["lenses"] = st.multiselect("OPTIONAL LENSES", ("uncertainty", "time", "space", "composition"))
                payload["anonymous"] = st.checkbox("RESPOND ANONYMOUSLY")
                payload["activate_next"] = st.checkbox("ACTIVATE THE NEXT STAGE")
            else:
                payload["reason"] = st.text_area("BRING SOMETHING, OR TELL US WHY YOU ENTERED.")
                payload["invite"] = st.text_area("ANYONE YOU WOULD LIKE TO INVITE? TELL US WHY.")
            payload["drop_requested"] = st.checkbox("I MAY WANT TO ADD A PRIVATE DROP AFTER AUTHENTICATION")
            submitted = st.form_submit_button("CONTINUE TO IDENTITY", width="stretch")
            if submitted:
                st.session_state["start_here_draft"] = {"mode": mode, "display_name": display_name, "payload": payload}
                record_event(st.session_state, "event_entry_drafted", mode)
                st.rerun()
        return

    st.markdown('<div class="entry-auth"><small>IDENTITY / AUTH</small><strong>YOUR CONTRIBUTION IS STILL A DRAFT.</strong><p>Persisting it creates or updates a provisional participant and records this act separately.</p></div>', unsafe_allow_html=True)
    persona_store = ProvisionalPersonaStore(st.session_state)
    active = persona_store.get_persona(str(st.session_state.get("active_persona_key", "")))
    if active:
        st.markdown(f'<div class="persona-emoji">{active.emoji_suffix_4}</div>', unsafe_allow_html=True)
        if st.button("PERSIST THIS CONTRIBUTION", type="primary", width="stretch"):
            _persist_start_here(repo, active, draft, invitation)
            st.rerun()
        return
    create_col, return_col = st.columns(2)
    with create_col:
        if st.button("CREATE EMOJI IDENTITY", type="primary", width="stretch"):
            result = mint_persona(
                persona_store, nickname=str(draft.get("display_name") or ""),
                key_factory=lambda: secrets.token_hex(16), clock=lambda: datetime.now(timezone.utc),
            )
            st.session_state["active_persona_key"] = result.persona.access_key
            st.rerun()
    with return_col:
        raw_key = st.text_input("RETURN WITH KEY / EMOJI", type="password")
        if st.button("AUTHENTICATE", disabled=not raw_key.strip(), width="stretch"):
            result = authenticate_persona(persona_store, raw_key, clock=lambda: datetime.now(timezone.utc))
            if result is None:
                st.error("KEY INVALID OR AMBIGUOUS")
            else:
                st.session_state["active_persona_key"] = result.persona.access_key
                st.rerun()


def _node_identities() -> dict[str, dict[str, str]]:
    if not _secrets_available():
        return {}
    try:
        return {
            str(node_id): {"access_key": str(config["access_key"])}
            for node_id, config in st.secrets["takeover_identities"].items()
            if str(config.get("access_key", "")).strip()
        }
    except (KeyError, TypeError, AttributeError):
        return {}


def render_activation_drop() -> None:
    identities = _node_identities()
    if not activation or activation not in identities:
        return
    with st.container(key=f"activation-drop-{activation}"):
        st.markdown(
            f'<div class="activation-drop-head"><small>INVITATION / {html.escape(activation.upper())}</small>'
            f'<strong>DROP / {html.escape(activation.upper())}</strong></div>',
            unsafe_allow_html=True,
        )
        st.write("A private encrypted drop is available for this seeded node.")
        authenticated = st.session_state.get("takeover_authenticated_drop") == activation
        if not authenticated:
            raw_key = st.text_input("DROP ACCESS KEY / EMOJI", type="password", key=f"drop-auth-{activation}")
            if st.button("AUTHENTICATE DROP", disabled=not raw_key.strip(), key=f"drop-auth-submit-{activation}", width="stretch"):
                if resolve_identity(raw_key, identities) != activation:
                    st.error("IDENTITY DOES NOT MATCH THIS DROP")
                else:
                    st.session_state["takeover_authenticated_drop"] = activation
                    record_event(st.session_state, "event_drop_authenticated", activation)
                    st.rerun()
            st.caption("THE QUERY PARAMETER SELECTS THE NODE; IT DOES NOT GRANT STORAGE ACCESS.")
            return
        s3, bucket, storage_identities, error = _drop_storage_context()
        if error:
            st.warning(error)
            return
        if st.button("OPEN PRIVATE DROP", key=f"drop-open-{activation}", type="primary", width="stretch"):
            resource_drop_dialog(activation, storage_identities, s3, bucket)


def _node_reference(raw: str) -> dict[str, str]:
    value = raw.strip()
    if not value:
        return {}
    if value.startswith(("http://", "https://")):
        return {"url": value, "filename": value.rstrip("/").rsplit("/", 1)[-1]}
    return {"cid": value}


def _media_data_url(reference: dict) -> str:
    path = Path(str(reference.get("path") or ""))
    mime_type = str(reference.get("mime_type") or "")
    if not path.is_file() or not mime_type.startswith("image/"):
        return ""
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _nodes_for_render(store: FileNodeStore) -> dict[str, dict]:
    nodes = store.list_nodes()
    for record in nodes.values():
        avatar = (record.get("node") or {}).get("avatar") or {}
        if avatar.get("path"):
            avatar["url"] = _media_data_url(avatar)
    return nodes


def render_node_editor(entity: Entity, store: FileNodeStore, repo) -> None:
    current = store.get(entity.id) or {}
    node = current.get("node") or {}
    avatar = node.get("avatar") or {}
    crop = avatar.get("crop") or {}
    sample = node.get("sample") or {}
    st.markdown("**AVATAR**")
    avatar_upload = st.file_uploader("DROP IMAGE", type=("jpg", "jpeg", "png", "webp"), key=f"node-avatar-{entity.id}")
    st.caption("THE RECTANGULAR ORIGINAL IS PRESERVED. THE CIRCLE IS A RENDERER DECISION.")
    avatar_url = st.text_input("OR AVATAR IMAGE URL", value=str(avatar.get("url") or entity.source or ""))
    crop_x, crop_y, crop_scale = st.columns(3)
    with crop_x:
        x = st.number_input("CROP X", 0.0, 1.0, float(crop.get("x", .5)), .05)
    with crop_y:
        y = st.number_input("CROP Y", 0.0, 1.0, float(crop.get("y", .5)), .05)
    with crop_scale:
        scale = st.number_input("CROP SCALE", 1.0, 4.0, float(crop.get("scale", 1.0)), .1)
    note = st.text_area("BIO / NOTE", value=str((node.get("text") or {}).get("text") or entity.metadata.get("bio") or ""), help="Markdown", max_chars=2000)
    st.markdown('<div class="node-preview-label">BIO / NOTE · PREVIEW</div>', unsafe_allow_html=True)
    st.markdown(note or "_Your note preview will appear here._")
    projected_practice = entity.metadata.get("practice") or ""
    if isinstance(projected_practice, list):
        projected_practice = ", ".join(str(item) for item in projected_practice)
    practice = st.text_input("PRACTICE", value=", ".join(node.get("practice") or []) or str(projected_practice), placeholder="photography, cyanotype")
    st.markdown("**SAMPLE · OPTIONAL**")
    sample_upload = st.file_uploader("DROP ONE SAMPLE", key=f"node-sample-{entity.id}")
    sample_reference = st.text_input("OR EXTERNAL LINK / CID", value=str(sample.get("url") or sample.get("cid") or entity.metadata.get("sample_url") or ""))
    sample_caption = st.text_input("SAMPLE CAPTION", value=str(sample.get("caption") or ""))
    authoritative = callable(getattr(repo, "upsert_player", None))
    has_avatar = bool(avatar_url.strip()) if authoritative else avatar_upload is not None or bool(avatar.get("path") or avatar.get("url") or avatar.get("cid"))
    if authoritative:
        st.caption("NOTION WRITE · USE A PUBLIC IMAGE URL. LOCAL FILE SELECTION IS NOT A DURABLE AVATAR REFERENCE.")
    state = population_state(
        "avatar" if has_avatar else "",
        note,
        practice,
        sample_reference,
    )
    if state.missing:
        st.caption(
            "NOTHING IS MANDATORY · ADD ANY ONE FIELD TO SAVE. "
            "NODE REMAINS IN POPULATION · MISSING TO COMPLETE: "
            + ", ".join(item.upper() for item in state.missing)
        )
    else:
        st.caption("ALL FOUR FIELDS ARE PRESENT · SAVE WILL MARK THE NODE READY.")
    save_column, cancel_column = st.columns([2, 1])
    with save_column:
        save = st.button(
            "INHABIT NODE", type="primary", disabled=not state.can_save,
            width="stretch", key=f"node-save-{entity.id}",
        )
    with cancel_column:
        if st.button("CANCEL", width="stretch", key=f"node-cancel-{entity.id}"):
            st.query_params.pop("node", None)
            st.rerun()
    if save:
        avatar_payload = dict(avatar)
        if avatar_upload is not None and not authoritative:
            avatar_payload = PublicNodeMediaStore(NODE_MEDIA).save_original(
                node_id=entity.id, filename=avatar_upload.name,
                content_type=avatar_upload.type or "application/octet-stream", data=avatar_upload.getvalue(),
            )
        avatar_payload["crop"] = {"x": x, "y": y, "scale": scale}
        sample_payload = {**_node_reference(sample_reference), "caption": sample_caption.strip()}
        if sample_upload is not None and not authoritative:
            sample_payload = {
                **PublicNodeMediaStore(NODE_MEDIA).save_sample(
                    node_id=entity.id, filename=sample_upload.name,
                    content_type=sample_upload.type or "application/octet-stream", data=sample_upload.getvalue(),
                ),
                "caption": sample_caption.strip(),
            }
        try:
            if authoritative:
                record = upsert_inhabited_node(
                    repo, entity, image_url=avatar_url, bio=note, practice=practice,
                    sample_url=str(sample_payload.get("url") or ""),
                    crop={"x": x, "y": y, "scale": scale},
                )
                st.session_state[f"node-upsert-result-{entity.id}"] = record
            else:
                record = store.save(
                    node_id=entity.id, avatar=avatar_payload, text=note,
                    practice=practice.split(","), sample=sample_payload,
                    clock=lambda: datetime.now(timezone.utc),
                )
        except ValueError as exc:
            st.error(str(exc).upper())
        else:
            persisted_stage = str(record.get("stage") or record.get("metadata", {}).get("node_stage") or "node_population")
            record_event(st.session_state, "event_node_inhabited", entity.id, persisted_stage)
            if authoritative:
                st.success("NODE UPSERTED · NOTION READ-BACK RECEIVED")
                st.json(record)
            else:
                st.rerun()


def render_ready_node(entity: Entity, record: dict | None) -> None:
    st.markdown('<div class="node-population-stage">NODE / READY</div>', unsafe_allow_html=True)
    node = (record or {}).get("node") or {}
    projected_avatar = entity.metadata.get("avatar")
    avatar = (
        projected_avatar
        if isinstance(projected_avatar, dict) and projected_avatar
        else (node.get("avatar") or {})
    )
    avatar_url = str(avatar.get("url") or _media_data_url(avatar) or "")
    bio = str(
        entity.metadata.get("bio")
        or (node.get("text") or {}).get("text")
        or ""
    )
    projected_practice = entity.metadata.get("practice") or ""
    practice_items = (
        [str(projected_practice)]
        if isinstance(projected_practice, str) and projected_practice.strip()
        else list(projected_practice or node.get("practice") or [])
    )
    practices = "".join(f'<span>{html.escape(str(item))}</span>' for item in practice_items)
    sample = node.get("sample") or {}
    sample_ref = str(
        entity.metadata.get("sample_url")
        or sample.get("url")
        or sample.get("cid")
        or ""
    )
    avatar_column, content_column = st.columns([1, 3], gap="large", vertical_alignment="top")
    with avatar_column:
        st.markdown("**AVATAR**")
        if avatar_url.startswith(("http://", "https://")):
            crop = avatar.get("crop") or {}
            st.markdown(
                f'<div class="inhabited-node-avatar" style="background-image:url({html.escape(json.dumps(avatar_url))});background-position:{100 * float(crop.get("x", .5)):.1f}% {100 * float(crop.get("y", .5)):.1f}%;background-size:{100 * float(crop.get("scale", 1)):.1f}%"></div>',
                unsafe_allow_html=True,
            )
        elif avatar.get("cid"):
            st.caption(f'AVATAR CID · {avatar["cid"]}')
        else:
            st.caption("NOT YET ADDED")
    with content_column:
        st.markdown("**BIO / NOTE**")
        st.markdown(bio or "_Not yet added._")
        st.markdown("**PRACTICE**")
        st.markdown(f'<div class="inhabited-node-practice">{practices}</div>', unsafe_allow_html=True)
        if not practice_items:
            st.caption("NOT YET ADDED")
        st.markdown("**SAMPLE**")
        if sample_ref.startswith(("http://", "https://")):
            st.markdown(
                f'<div class="inhabited-node-sample"><small>{html.escape(str(sample.get("type") or "LINK").upper())}</small>'
                f'<strong>{html.escape(str(sample.get("caption") or sample_ref))}</strong>'
                f'<a href="{html.escape(sample_ref)}" target="_blank" rel="noopener noreferrer">OPEN SAMPLE ↗</a></div>',
                unsafe_allow_html=True,
            )
        elif sample_ref:
            st.markdown(f'<div class="inhabited-node-sample"><small>{html.escape(str(sample.get("type") or "OBJECT").upper())}</small><strong>{html.escape(str(sample.get("caption") or sample_ref))}</strong><span>{html.escape(sample_ref)}</span></div>', unsafe_allow_html=True)
        else:
            st.caption("NOT YET ADDED")
    if not any((avatar_url, bio, practice_items, sample_ref)):
        if entity.label:
            st.write(entity.label)
        st.caption("REGISTERED KERNEL NODE")


@st.dialog(t("node"), width="large")
def node_dialog(entity: Entity, participant_id: str | None, repo) -> None:
    st.markdown(f'<div class="node-kind">{html.escape(entity_type_label(entity.type))}</div>', unsafe_allow_html=True)
    st.header(entity.title)
    stage = node_stage(entity)
    store = FileNodeStore(NODE_REGISTRY)
    record = store.get(entity.id)
    stage_label = "POPULATION" if stage == "node_population" else stage.replace("_", " ").upper()
    st.markdown(
        f'<div class="node-population-stage">NODE STAGE · {html.escape(stage_label)} / {html.escape(entity.status.upper())}</div>',
        unsafe_allow_html=True,
    )
    if stage == "node_population":
        if participant_id == entity.id:
            st.write("This node is waiting for you.")
            st.caption("WRITE CAPABILITY REQUIRED TO INHABIT THIS NODE.")
        else:
            st.write("This node is waiting for them.")
            if entity.label:
                st.write(entity.label)
    elif stage == "ready":
        render_ready_node(entity, record)
    elif stage == "invited":
        st.write("This node enters through START HERE when its invitation is activated.")
    elif stage == "contributing":
        st.write("The inhabited node, private drop and active relations are available at this stage.")
    else:
        if entity.label:
            st.write(entity.label)
    st.caption(f'{t("registry_id")} · {entity.id}')


@st.dialog("INHABIT NODE", width="large")
def owned_node_dialog(repo, player: dict) -> None:
    code = str((player.get("metadata") or {}).get("invitation_code") or "")
    draft_key = f"node-population-draft-{player['player_id']}"
    draft = dict(st.session_state.get(draft_key) or {})
    st.markdown(f'<div class="node-kind">INVITATION · {html.escape(code)}</div>', unsafe_allow_html=True)
    st.header(str(player.get("name") or "INVITED PLAYER"))
    st.write(
        "You have been invited into an existing network. Add only what is useful now; "
        "the node can continue to change after it is inhabited."
    )
    with st.form(f"invited-node-{player['player_id']}"):
        avatar_upload = st.file_uploader(
            "UPLOAD AVATAR",
            type=("jpg", "jpeg", "png", "webp"),
            key=f"owned-avatar-{player['player_id']}",
        )
        image_url = st.text_input("AVATAR / IMAGE URL", value=str(draft.get("image_url") or player.get("image_url") or ""))
        bio = st.text_area("BIO / NOTE", value=str(draft.get("bio") or player.get("bio") or ""))
        practice = st.text_input("PRACTICE", value=str(draft.get("practice") or player.get("practice") or ""))
        sample_url = st.text_input("ONE REPRESENTATIVE SAMPLE / URL", value=str(draft.get("sample_url") or player.get("sample_url") or ""))
        state = population_state(
            image_url or ("pending-upload" if avatar_upload is not None else ""),
            bio,
            practice,
            sample_url,
        )
        if state.missing:
            st.caption(
                "NOTHING IS MANDATORY · ADD ANY ONE FIELD TO SAVE. "
                "NODE REMAINS IN POPULATION · MISSING TO COMPLETE: "
                + ", ".join(item.upper() for item in state.missing)
            )
        else:
            st.caption("ALL FOUR FIELDS ARE PRESENT · SAVE WILL MARK THE NODE READY.")
        submitted = st.form_submit_button(
            "SAVE / INHABIT NODE",
            type="primary",
            width="stretch",
            disabled=not state.can_save,
        )
    if submitted:
        st.session_state[draft_key] = {
            "image_url": image_url,
            "bio": bio,
            "practice": practice,
            "sample_url": sample_url,
        }
        record_event(st.session_state, "event_node_edited", str(player["player_id"]))
        try:
            persisted_image_url = image_url.strip()
            if avatar_upload is not None:
                media_store, storage_error = _public_avatar_store()
                if storage_error or media_store is None:
                    raise ValueError(storage_error or "PUBLIC AVATAR STORAGE IS UNAVAILABLE")
                uploaded_avatar = media_store.save_avatar(
                    player_id=str(player["player_id"]),
                    filename=avatar_upload.name,
                    content_type=avatar_upload.type or "application/octet-stream",
                    data=avatar_upload.getvalue(),
                )
                persisted_image_url = uploaded_avatar.url
            metadata = dict(player.get("metadata") or {})
            metadata["invitation_registered_at"] = datetime.now(timezone.utc).isoformat()
            result = upsert_player_verified(repo, PlayerPopulation(
                player_id=str(player["player_id"]),
                name=str(player["name"]),
                label=str(player.get("label") or "Person • Alien"),
                image_url=persisted_image_url,
                bio=bio.strip(),
                practice=practice.strip(),
                sample_url=sample_url.strip(),
                metadata=metadata,
                initial_condition=dict(player.get("initial_condition") or {}),
                project_stage="application",
                node_stage=state.node_stage,
                status="active",
                network_state="active",
                visibility="public",
            ))
            record_event(st.session_state, "event_save_succeeded", str(player["player_id"]), "read-back verified")
            st.session_state.pop(draft_key, None)
            if state.complete:
                st.session_state["completed-node-population"] = {
                    "player_id": player["player_id"],
                    "name": player["name"],
                    "code": code,
                    "result": result,
                }
                st.session_state.pop("saved-node-population", None)
            else:
                st.session_state["saved-node-population"] = {
                    "player_id": player["player_id"],
                    "name": player["name"],
                    "missing": state.missing,
                }
            st.rerun()
        except Exception as exc:
            record_event(st.session_state, "event_save_failed", str(player["player_id"]), type(exc).__name__)
            st.error(f"REGISTRATION FAILED · {type(exc).__name__}: {exc}")


def resolve_capability_player(repo, player_registry_status: str) -> PlayerResolution:
    capability = str(st.query_params.get("c", "") or "")
    if not capability:
        return PlayerResolution("missing")
    return resolve_capability(
        repo, capability, registry_status=player_registry_status
    )


def resolve_entry_invitation(repo, player_registry_status: str) -> InvitationResolution:
    code = str(st.query_params.get("i", "") or "")
    if not code:
        return InvitationResolution("missing")
    return resolve_invitation(repo, code, registry_status=player_registry_status)


@st.dialog(t("connection"), width="large")
def relation_dialog(relation, entities: list[Entity]) -> None:
    names = {entity.id: entity.title for entity in entities}
    source = names.get(relation.source, relation.source)
    target = t("start_here") if relation.target == "*" else names.get(relation.target, relation.target)
    st.markdown(f'<div class="node-kind">{t("active_relation")}</div>', unsafe_allow_html=True)
    st.header(f"{source} ↔ {target}")
    st.markdown(f'<div class="relation-role">{html.escape(relation.type.upper())}</div>', unsafe_allow_html=True)
    st.caption(f'{t("stage")} · {relation.stage.upper()}   /   {t("status")} · {relation.status.upper()}')
    st.write(t("relation_explainer"))
    st.caption(f'{t("registry_id")} · {relation.id}')


@st.dialog(t("state_of_art"), width="large")
def state_dialog(entities: list[Entity], relations) -> None:
    entity_status = {entity.id: entity.status for entity in entities}
    active = sum(
        relation.status == "active"
        and entity_status.get(relation.source) == "active"
        and entity_status.get(relation.target) == "active"
        for relation in relations
    )
    connectivity = (1 + len(relations)) / len(entities) if entities else 0
    state_counts = {
        status: sum(entity.status == status for entity in entities)
        for status in ("active", "latent_known", "latent_private", "unknown")
    }
    st.markdown(f'<div class="node-kind">{t("network_state")}</div>', unsafe_allow_html=True)
    st.header(t("state_of_art"))
    st.write(t("state_of_art_intro"))
    st.markdown(
        f'<div class="state-dialog-stats"><span>{state_counts["active"]} {t("active_people").lower()}</span>'
        f'<span>{state_counts["latent_known"]} {t("latent_known").lower()}</span>'
        f'<span>{state_counts["latent_private"]} {t("latent_private").lower()}</span>'
        f'<span>{state_counts["unknown"]} {t("unknown").lower()}</span>'
        f'<span>{len(relations)} {t("connections").lower()}</span>'
        f'<span>{connectivity:.2f} {t("connectivity").lower()}</span>'
        f'<span>{active} {t("active_relations").lower()}</span></div>',
        unsafe_allow_html=True,
    )
    for key, description in (
        ("node", "node_question"),
        ("connection", "connection_question"),
        ("contribution", "contribution_question"),
        ("state_of_art", "state_question"),
    ):
        st.markdown(f'**{t(key)}** → {t(description)}')


def render_nav(current: str) -> None:
    st.markdown(f'<div class="takeover-brand">{t("project_name")}</div>', unsafe_allow_html=True)
    with st.container(key="top-nav"):
        columns = st.columns([1, 1, 1, 1, 1, 1, 2])
        for column, label, key in zip(columns, (t("process"), t("timeline"), t("needs"), t("resources"), t("order_art"), t("voices")), ("network", "timeline", "necessities", "resources", "order-art", "voices")):
            with column:
                st.button(label, key=f"nav-{key}", disabled=current == key, on_click=switch_view, args=(key,))


def render_sidebar_voice_statistics() -> None:
    metrics = language_status_metrics()
    eligible_recordings = {utterance.key for utterance in UTTERANCES if utterance.weight >= 30}
    completed_recordings = {
        event["target"] for event in list_events(st.session_state)
        if event.get("label_key") == "event_recording_ready" and event.get("target") in eligible_recordings
    }
    proposals = st.session_state.get("takeover_translation_proposals", [])
    translation_capacity = len(UTTERANCES) * (len(VOICE_LANGUAGES) - 1)
    status_totals = {status: sum(item[status] for item in metrics.values()) for status in ("CANONICAL", "PROVISIONAL", "UNTRANSLATED")}
    status_capacity = sum(status_totals.values()) or 1
    st.markdown(f'<div class="sidebar-analysis-title">{t("voices_statistics")}</div>', unsafe_allow_html=True)
    for label, value, capacity in (
        (t("recordings_complete"), len(completed_recordings), len(eligible_recordings)),
        (t("translation_proposals"), len(proposals), translation_capacity),
        (t("corpus_status"), status_totals["CANONICAL"] + status_totals["PROVISIONAL"], status_capacity),
    ):
        st.markdown(f'<div class="sidebar-stat"><small>{label}</small><strong>{value} / {capacity}</strong><span>{100 * value / max(1, capacity):.1f}%</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-analysis-subtitle">{t("language_status")}</div>', unsafe_allow_html=True)
    for code in VOICE_LANGUAGES:
        counts = metrics[code]
        total = sum(counts.values()) or 1
        segments = "".join(f'<i class="status-{status.lower()}" style="width:{100 * count / total:.2f}%"></i>' for status, count in counts.items() if count)
        detail = " · ".join(f'{status} {100 * count / total:.0f}%' for status, count in counts.items() if count)
        st.markdown(f'<div class="sidebar-language-metric"><strong>{language_term(code)}</strong><div class="status-bar">{segments}</div><small>{detail}</small></div>', unsafe_allow_html=True)


def render_sidebar_call_information() -> None:
    call = load_call(CALL)
    paragraphs = "".join(f'<p>{html.escape(str(paragraph))}</p>' for paragraph in call["paragraphs"])
    st.markdown(f'<section class="sidebar-call"><small>{html.escape(str(call["title"]).upper())}</small>{paragraphs}<strong>{html.escape(str(call["emphasis"]))}</strong></section>', unsafe_allow_html=True)


def render_sidebar_time_mapping() -> None:
    payload = load_trajectory(TRAJECTORY)
    plan = payload["plan"]
    event_rows = build_time_mapping_rows(payload)
    figure = build_time_mapping_figure(payload)
    figure.update_layout(height=360, margin={"l": 42, "r": 12, "t": 20, "b": 45}, showlegend=False, title=None)
    figure.update_xaxes(title="u · LINEAR")
    figure.update_yaxes(title="q · NONLINEAR")
    st.markdown(f'<div class="sidebar-analysis-title">{t("time_mapping")}</div>', unsafe_allow_html=True)
    st.write(t("time_mapping_note"))
    st.latex(r"u_i=\frac{d_i-d_0}{H},\quad q_i=f(u_i),\quad \Delta_i=q_i-u_i")
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
    st.markdown(f'<div class="sidebar-analysis-title">{t("datasets")}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-stat">'
        f'<small>{t("phase")}</small><strong>{t("application")}</strong>'
        f'<span>{html.escape(str(plan.get("temporal_mode") or ""))}</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.dataframe([{
        "START": plan.get("start_date"),
        "HORIZON": plan.get("horizon_days"),
        "UNIT": plan.get("time_unit"),
        "LANDING": plan.get("destination_label"),
    }], use_container_width=True, hide_index=True)
    anchor_rows = [
        {"ANCHOR": str(anchor[0]), "q": float(anchor[1])}
        for anchor in plan.get("qualitative_anchors") or []
    ]
    st.markdown('<div class="sidebar-analysis-subtitle">QUALITATIVE ANCHORS</div>', unsafe_allow_html=True)
    st.dataframe(anchor_rows, use_container_width=True, hide_index=True)
    st.markdown(f'<div class="sidebar-analysis-subtitle">{t("trajectory_dataset")}</div>', unsafe_allow_html=True)
    st.dataframe([
        {
            "DATE": row["date"],
            "EVENT": row["title"],
            "TYPE": row["type"],
            "u": round(row["linear"], 3),
            "q": round(row["nonlinear"], 3),
            "Δ": round(row["residual"], 3),
            "VISIBILITY": row["visibility"],
        }
        for row in event_rows
    ], use_container_width=True, hide_index=True)


def render_sidebar_resource_datasets() -> None:
    trajectory = load_trajectory(TRAJECTORY)
    resource_plan = load_resources(RESOURCES)
    trajectory_rows = [
        {
            "id": item.get("id"),
            "date": item.get("date"),
            "type": item.get("type"),
            "title": item.get("title"),
            "q": item.get("time_parameter"),
        }
        for item in sorted(
            trajectory["primitives"],
            key=lambda value: float(value.get("time_parameter", 0)),
        )
    ]
    st.markdown('<div class="sidebar-analysis-title">VOLUME SCALING</div>', unsafe_allow_html=True)
    st.number_input(
        "SCALING FACTOR · s",
        min_value=0.01,
        max_value=10.0,
        value=1.0,
        step=0.1,
        format="%.2f",
        key="resource-volume-scale",
        help="V̂ₛ(t) = s · V(t) / V(now)",
    )
    st.caption("V̂ₛ(t) = s · V(t) / V(now)")
    with st.expander(t("datasets"), expanded=False):
        st.markdown(f'<div class="sidebar-analysis-subtitle">{t("allocated_dataset")}</div>', unsafe_allow_html=True)
        st.dataframe(resource_plan["allocated_resources"]["observations"], width="stretch", hide_index=True)
        st.markdown(f'<div class="sidebar-analysis-subtitle">{t("intentions_dataset")}</div>', unsafe_allow_html=True)
        st.dataframe(resource_plan["investment_intentions"], width="stretch", hide_index=True)
        st.markdown(f'<div class="sidebar-analysis-subtitle">{t("trajectory_dataset")}</div>', unsafe_allow_html=True)
        st.dataframe(trajectory_rows, width="stretch", hide_index=True)


def render_sidebar(current: str, mode: str, database: RegistryDiagnostics) -> None:
    with st.sidebar:
        st.title(t("project_name"))
        st.caption(t("project_navigation"))
        for label, key in (
            (t("process"), "network"),
            (t("timeline"), "timeline"),
            (t("needs"), "necessities"),
            (t("resources"), "resources"),
            (t("order_art"), "order-art"),
            (t("voices"), "voices"),
        ):
            st.button(
                label,
                key=f"sidebar-{key}",
                disabled=current == key,
                use_container_width=True,
                on_click=switch_view,
                args=(key,),
            )
        st.divider()
        st.caption(f'{t("registry")} · {mode.upper()}')
        st.caption(t("development_interface"))
        st.markdown('<div class="event-log-title">DATABASE STATUS</div>', unsafe_allow_html=True)
        st.caption(
            f"{database.status.upper()} · {database.authority.upper()} · "
            f"{database.entity_count} NODES · {database.relation_count} RELATIONS"
        )
        if database.error_type:
            st.warning(f"DATABASE READ FAILED · {database.error_type}")
        elif database.status == "empty":
            st.info("NO ACTIVE GRAPH ROWS RETURNED")
        if current == "network":
            render_sidebar_call_information()
        elif current == "timeline":
            render_sidebar_time_mapping()
        elif current == "resources":
            render_sidebar_resource_datasets()
        elif current == "voices":
            render_sidebar_voice_statistics()
        st.markdown(f'<div class="event-log-title">{t("event_log")}</div>', unsafe_allow_html=True)
        for event in reversed(list_events(st.session_state)):
            occurred = str(event.get("occurred_at") or "")[11:19]
            label_key = str(event.get("label_key") or "")
            label = t(label_key) if label_key in REGISTRY else label_key
            target = html.escape(str(event.get("target") or ""))
            detail = html.escape(str(event.get("detail") or ""))
            suffix = " · ".join(value for value in (target, detail) if value)
            st.markdown(f'<div class="event-log-row"><time>{occurred} UTC</time><strong>{html.escape(label)}</strong>{f"<span>{suffix}</span>" if suffix else ""}</div>', unsafe_allow_html=True)


def render_network(
    repo,
    mode: str,
    database: RegistryDiagnostics,
    capability_player: dict | None = None,
    invitation: InvitationRecord | None = None,
) -> None:
    entities, relations = list(database.entities), list(database.relations)
    if invitation:
        st.info(
            f"{invitation.invited_by.upper()} OPENED THIS DOOR FOR YOU · "
            f"INVITE {invitation.code} · START HERE"
        )
    process = "".join(
        f'<p>{html.escape(t(key))}</p>'
        for key in ("take_wall", "take_oven", "take_sound", "take_restaurant", "take_night", "take_web")
    )
    manifesto = "<br>".join(
        html.escape(t(key))
        for key in ("manifesto_remains", "manifesto_doors", "manifesto_listen", "manifesto_build")
    )
    manifesto += "<br><br>" + "<br>".join(
        html.escape(t(key)) for key in ("manifesto_live", "manifesto_grows")
    )
    left, right = st.columns([0.8, 1.55], gap="large")
    with left:
        st.markdown('<div class="takeover-copy">', unsafe_allow_html=True)
        st.title(t("project_name"))
        st.markdown(f'<div class="takeover-kicker">{t("interactive_progress")}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<section class="application-state"><strong>{t("application_window")} / {t("open")}</strong>'
            f'<span>{t("before_submission")}</span></section>',
            unsafe_allow_html=True,
        )
        uncertainty_rows = "".join(
            f'<div><span>{t(label)}</span><b>{t(state)}</b></div>'
            for label, state in (
                ("participants", "unknown"),
                ("production_budget", "none_secured"),
                ("jury", "unknown"),
                ("selection", "unknown"),
                ("response_time", "unknown"),
                ("exhibition_feasibility", "conditional"),
                ("future_contributors", "open"),
                ("next_state", "unresolved"),
            )
        )
        st.markdown(
            f'<section class="uncertainty-state"><small>{t("current_state")}</small>{uncertainty_rows}'
            f'<p>{t("uncertainty_statement")}</p>'
            f'<a class="application-file-action" href="{APPLICATION_FILE_URL}" target="_blank" '
            f'rel="noopener noreferrer" aria-label="{html.escape(t("open_application_file"))}">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2h8l5 5v15H6V2Zm8 2.7V8h3.3L14 4.7ZM9 12v2h4.6l-2.3 2.3 1.4 1.4L17.4 13l-4.7-4.7-1.4 1.4 2.3 2.3H9Z"/></svg>'
            f'<span><small>APPLICATION · PDF</small><strong>{html.escape(t("open_application_file"))}</strong></span>'
            '<b aria-hidden="true">↗</b></a></section>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.caption(
            "GRAPH SOURCE · DATABASE / GENERATED · "
            f"{len(entities)} NODES · {len(relations)} RELATIONS"
        )
        owner_id = str((capability_player or {}).get("player_id") or "")
        write_capability = (
            str(st.query_params.get("c", "") or "") if owner_id else ""
        )
        st.html(
            build_graph_html(
                entities, relations, t("start_here"), t("state_of_art"),
                t("nodes"), t("connections"), t("connectivity"),
                t("active_relations"), t("additions_opening_next"),
                t("active_people"), t("latent_known"), t("latent_private"), t("unknown"),
                owner_id or None,
                write_capability,
                connectivity_history(entities, relations),
                invitation.code if invitation else "",
            )
        )
    render_activation_drop()
    st.markdown(
        '<section class="takeover-three-blocks">'
        f'<article class="takeover-process">{process}</article>'
        f'<article class="takeover-manifesto">{manifesto}</article>'
        f'<article class="takeover-entry"><strong>{html.escape(t("landing_action"))}</strong>'
        f'<span>{html.escape(t("open_node"))}</span>{footer_html()}</article>'
        '</section>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<section class="handoff">{t("pass_it_on")}</section>', unsafe_allow_html=True)
    listening_payload = load_listening(LISTENING)
    listening = listening_payload["suggested_listening"]
    st.markdown(
        f'<section class="listening"><small>{html.escape(str(listening["title"]).upper())}</small>'
        f'<span>{len(listening["items"])} RECORDS · {html.escape(str(listening["status"]).upper())}</span></section>',
        unsafe_allow_html=True,
    )
    if listening_payload.get("presentation", {}).get("show_addendum", False):
        st.markdown(
            f'<section class="listening-addendum"><small>ADDENDUM / {html.escape(str(listening["status"]).upper())}</small>'
            f'<h2>{html.escape(str(listening["title"]))}</h2><p>{html.escape(str(listening["description"]))}</p></section>',
            unsafe_allow_html=True,
        )
        for item in listening["items"]:
            artist = item.get("artist") or item.get("artist_visible") or ""
            title = item.get("title") or item.get("title_visible") or ""
            performer = item.get("performer") or ""
            relation_labels = " · ".join(str(value).replace("_", " ").upper() for value in item.get("relation", []))
            st.markdown(
                '<article class="listening-item">'
                f'<small>{html.escape(str(item["status"]).replace("_", " ").upper())} / {html.escape(str(item["format"]).upper())}</small>'
                f'<h3>{html.escape(str(title))}</h3><strong>{html.escape(str(artist))}</strong>'
                f'{f"<span>{html.escape(str(performer))}</span>" if performer else ""}'
                f'<p>{html.escape(str(item["note"]))}</p><footer>{html.escape(relation_labels)}</footer>'
                '</article>',
                unsafe_allow_html=True,
            )
    if str(st.query_params.get("door", "") or "") == "access":
        record_event_once(st.session_state, "access-door-open", "event_access_opened")
        access_door(repo, invitation)
    requested = str(st.query_params.get("node", "") or "")
    selected = next((item for item in entities if item.id == requested), None)
    if selected:
        record_event_once(st.session_state, f"node-open-{selected.id}", "event_node_opened", selected.id)
        if str((capability_player or {}).get("player_id") or "") == selected.id:
            owned_node_dialog(repo, capability_player)
        else:
            node_dialog(selected, None, repo)
    requested_relation = str(st.query_params.get("relation", "") or "")
    selected_relation = next((item for item in relations if item.id == requested_relation), None)
    if selected_relation:
        record_event_once(
            st.session_state,
            f"relation-open-{selected_relation.id}",
            "event_connection_opened",
            selected_relation.id,
            selected_relation.type,
        )
        relation_dialog(selected_relation, entities)
    if str(st.query_params.get("state", "") or "") == "art":
        record_event_once(st.session_state, "state-of-art-open", "event_state_opened")
        state_dialog(entities, relations)
    render_resource_drop_link()
    if os.getenv("TAKEOVER_ADMIN_MODE", "").strip() == "1":
        render_admin(repo, mode)


def render_admin(repo, mode: str) -> None:
    with st.expander(t("developer_add"), expanded=False):
        st.caption(t("admin_note"))
        with st.form("add-node-form", clear_on_submit=True):
            kind = st.selectbox(t("entity_type"), ENTITY_TYPES, format_func=entity_type_label)
            title = st.text_input(t("name_title"))
            entity_id = st.text_input(t("id"), placeholder="ave")
            label = st.text_input(t("label"), placeholder="artist")
            stage = st.selectbox(t("stage"), STAGES)
            source = st.text_input(t("image_audio_url"), placeholder="https://…")
            submitted = st.form_submit_button(t("add_entity"), use_container_width=True)
        if submitted:
            clean_id = re.sub(r"[^a-z0-9_-]+", "-", entity_id.strip().lower()).strip("-")
            try:
                repo.add_entity(Entity(clean_id, kind, title.strip(), label.strip(), stage, "active", source.strip()))
            except ValueError as exc:
                st.error(str(exc))
            else:
                record_event(st.session_state, "event_entity_added", clean_id)
                st.success(f'{title} · {t("registry")} · {mode.upper()}')
                st.rerun()


def render_timeline() -> None:
    st.markdown(f'<div class="section-head">{t("timeline")} · {t("application")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="timeline-phase">{t("phase")}: {t("application")}</div>', unsafe_allow_html=True)
    payload = load_trajectory(TRAJECTORY)
    st.caption(t("timeline_proposition"))
    focus_label = st.segmented_control(
        "FOCUS ON",
        options=("DONE", "TO DO"),
        default="TO DO",
        key="timeline-focus",
    )
    st.plotly_chart(
        build_timeline_figure(
            payload,
            focus="done" if focus_label == "DONE" else "to_do",
        ),
        width="stretch",
        theme=None,
        config={"displayModeBar": False, "scrollZoom": False},
    )
    st.caption(f'STATIC · {t("timeline_source")}')


def render_necessities(repo) -> None:
    st.markdown(f'<div class="section-head">{t("necessities_title")}</div>', unsafe_allow_html=True)
    st.caption(t("need_stage_state"))
    necessities = repo.list_necessities()
    st.markdown(f'<div class="necessity necessity-head"><strong>{t("need")}</strong><span>{t("stage")}</span><span>{t("state")}</span></div>', unsafe_allow_html=True)
    for item in necessities:
        name = t(item.title) if item.title in REGISTRY else item.title
        stage = t(item.stage) if item.stage in REGISTRY else item.stage.upper()
        status = t(item.status) if item.status in REGISTRY else item.status.upper()
        if item.title == "application" and item.status == "to_submit":
            status = f'{t("to_submit")} → {t("done")}'
        st.markdown(
            f'<div class="necessity{" dormant" if item.status == "not_yet_activated" else ""}"><strong>{html.escape(name)}</strong><span class="stage">{html.escape(stage)}</span><span class="status">{html.escape(status)}</span></div>',
            unsafe_allow_html=True,
        )
    if not necessities:
        st.info(t("no_necessities"))


def render_resources(repo) -> None:
    trajectory = load_trajectory(TRAJECTORY)
    resource_plan = load_resources(RESOURCES)
    st.markdown(f'<div class="section-head">{t("resources")} · {t("application")}</div>', unsafe_allow_html=True)
    st.write(t("resources_intro"))
    st.caption(t("observed_intention"))
    actions = (
        ("buy", "resource_action_buy", "resource_action_buy_explanation"),
        ("donate", "resource_action_donate", "resource_action_donate_explanation"),
        ("invest", "resource_action_invest", "resource_action_invest_explanation"),
        ("bet", "resource_action_bet", "resource_action_bet_explanation"),
        ("play", "resource_action_play", "resource_action_play_explanation"),
    )
    with st.container(key="resource-actions"):
        for column, (action, label_key, explanation_key) in zip(st.columns(5), actions):
            with column:
                pressed = st.button(t(label_key), key=f"resource-action-{action}", width="stretch")
                st.markdown(f'<p class="resource-action-explanation">{html.escape(t(explanation_key))}</p>', unsafe_allow_html=True)
                if pressed:
                    record_event(st.session_state, "event_resource_action", action, "rc2-pathway-visible")
                    st.caption(t("resource_action_pending"))
    bucket_objects, bucket_error = _bucket_objects()
    total_bytes = sum(int(item.get("Size", 0)) for item in bucket_objects)
    field = load_resource_field(RESOURCE_FIELD)
    active_people = sum(entity.status == "active" for entity in with_rc0_seeds(repo.list_entities(), repo.list_relations())[0])
    activation_events = sum(event.get("label_key") == "event_invitation_activation" for event in list_events(st.session_state))
    rows = resource_rows(
        field, active_people=active_people, bucket_bytes=total_bytes,
        bucket_files=len(bucket_objects), activation_events=activation_events,
    )
    application = field["application"]
    transition_suffix = f' · {application["submitted_at"]}' if application.get("submitted_at") else " · TIMESTAMP UNSET"
    st.markdown(
        f'<section class="application-transition"><span>APPLICATION / OPEN</span><b>→</b>'
        f'<span class="{application["state"]}">APPLICATION / SUBMITTED{html.escape(transition_suffix)}</span></section>',
        unsafe_allow_html=True,
    )
    for row in rows:
        provenance = row.get("provenance") or {}
        provenance_text = " · ".join(str(value) for value in (provenance.get("who"), provenance.get("when"), provenance.get("condition")) if value)
        st.markdown(
            f'<article class="resource-field-row state-{html.escape(row["state"])}">'
            f'<strong>{html.escape(row["label"])}</strong><i></i><span>{html.escape(row["value"])}</span>'
            f'<small>{html.escape(provenance_text or "PROVENANCE · OPEN")}</small></article>',
            unsafe_allow_html=True,
        )
    allocated_metric, volume_metric, files_metric = st.columns(3)
    allocated_metric.metric("BUCKET OF DOUGH", "€0")
    volume_metric.metric("BUCKET OF GOLD", f"{total_bytes / 1024 / 1024:.2f} MB" if total_bytes else "0 B")
    files_metric.metric("TOTAL FILES", len(bucket_objects))
    if bucket_error:
        st.caption(bucket_error)
    volume_scale = float(st.session_state.get("resource-volume-scale", 1.0))
    st.caption(f"SHARED SCALE · ALLOCATED EUR = 0 · V̂ₛ(t) = {volume_scale:g} · V(t) / V(now) · INTENTION HAS NO VALUE")
    st.plotly_chart(
        build_combined_resources_figure(
            trajectory, resource_plan, bucket_objects, volume_scale=volume_scale
        ),
        width="stretch",
        theme=None,
        config={"displayModeBar": False, "scrollZoom": False},
    )


def render_order_art() -> None:
    st.markdown(f'<div class="section-head">{t("order_art")}</div>', unsafe_allow_html=True)
    st.write(t("order_art_intro"))
    st.markdown(
        f'<section class="order-art-empty"><small>{html.escape(t("order_art_status"))}</small>'
        f'<strong>{html.escape(t("order_art_empty"))}</strong></section>',
        unsafe_allow_html=True,
    )


def footer_html() -> str:
    telegram_icon = (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21.5 3.2 18.3 19c-.2 1.1-.9 1.4-1.8.9l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.4-5 9.1-8.2c.4-.4-.1-.6-.6-.2L5.8 12.8 1 11.3c-1-.3-1.1-1 .2-1.5L20 2.5c.9-.3 1.7.2 1.5.7Z"/></svg>'
    )
    filebase_icon = (
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 2 8 4.3v11.4L12 22l-8-4.3V6.3L12 2Zm0 2.3L6.2 7.4 12 10.6l5.8-3.2L12 4.3Zm-6 5v7.2l5 2.7V12L6 9.3Zm7 9.9 5-2.7V9.3L13 12v7.2Z"/></svg>'
    )
    return (
        '<footer class="takeover-footer"><span>FOLLOW THE SIGNAL</span><nav>'
        f'<a href="https://t.me/takeover_process_bot" target="_blank" rel="noopener noreferrer" aria-label="Open TAKE OVER on Telegram">{telegram_icon}<strong>TELEGRAM</strong><small>CHANNEL / BOT ↗</small></a>'
        f'<span class="takeover-footer-disabled" aria-disabled="true">{filebase_icon}<strong>FILEBASE</strong><small>BUCKET / DORMANT</small></span>'
        '</nav></footer>'
    )


def set_language(language: str) -> None:
    previous = st.session_state.get("takeover_language", "en")
    st.session_state["takeover_language"] = language
    record_event(st.session_state, "event_language_changed", f"{previous} → {language}")


def log_reading_languages() -> None:
    selected = st.session_state.get("voices-reading-languages", [])
    record_event(st.session_state, "event_reading_languages", ", ".join(str(code) for code in selected))


@st.dialog(t("voice_recording"), width="large")
def voice_recording_dialog(utterance) -> None:
    st.markdown(f'<div class="recording-utterance">{html.escape(utterance.text(language))}</div>', unsafe_allow_html=True)
    st.write(t("recording_prompt"))
    recording = st.audio_input(t("start_recording"), key=f"visitor-voice-recording-{utterance.key}")
    if recording is not None:
        record_event_once(st.session_state, f"recording-ready-{utterance.key}", "event_recording_ready", utterance.key)
        st.audio(recording)
        st.caption(t("recording_ready"))


@st.dialog(t("add_translation"), width="large")
def translation_proposal_dialog(utterance) -> None:
    target_languages = tuple(code for code in VOICE_LANGUAGES if code != "en")
    target = st.selectbox(t("translation_language"), target_languages, format_func=language_term, key=f"translation-language-{utterance.key}")
    st.caption(t("original"))
    st.markdown(f'<div class="translation-source">{html.escape(utterance.canonical)}</div>', unsafe_allow_html=True)
    st.caption(t("current_translation"))
    st.markdown(f'<div class="translation-current">{html.escape(utterance.text(target))}</div>', unsafe_allow_html=True)
    with st.form(f"translation-proposal-{utterance.key}", clear_on_submit=True):
        proposal = st.text_area(t("your_version"), key=f"translation-version-{utterance.key}")
        submitted = st.form_submit_button(t("propose_translation"), use_container_width=True)
    if submitted:
        if not proposal.strip():
            st.error(t("translation_required"))
        else:
            record_translation_proposal(st.session_state, utterance.key, target, proposal)
            record_event(st.session_state, "event_translation_saved", utterance.key, target)
            st.success(t("translation_saved"))


def render_voices() -> None:
    st.markdown('<main class="voices">', unsafe_allow_html=True)
    st.markdown(f'<div class="voices-head"><h1>{t("voices")}</h1><p>{t("voices_intro")}</p></div>', unsafe_allow_html=True)
    with st.container(key="voices-language-rail"):
        language_items = list(LANGUAGES.items())
        for row_start in range(0, len(language_items), 4):
            columns = st.columns(4)
            for column, (code, label) in zip(columns, language_items[row_start:row_start + 4]):
                with column:
                    st.button(
                        language_term(code),
                        key=f"voice-language-{code}",
                        type="primary" if code == language else "secondary",
                        use_container_width=True,
                        on_click=set_language,
                        args=(code,),
                    )
    st.markdown(f'<div class="voice-contribution-key"><span>🎙</span><strong>{t("record_voice")}</strong><span>+</span><strong>{t("add_translation")}</strong><small>{t("voice_contribution_intro")}</small></div>', unsafe_allow_html=True)
    reading_languages = st.multiselect(
        t("languages_to_read"),
        options=VOICE_LANGUAGES,
        default=VOICE_LANGUAGES,
        format_func=language_term,
        key="voices-reading-languages",
        on_change=log_reading_languages,
    )
    for utterance in UTTERANCES:
        variants = []
        for code in reading_languages:
            variants.append(f'<span><b>{code.upper()} · {utterance.status(code)}</b>{html.escape(utterance.text(code))}</span>')
        weight_class = 5 if utterance.weight >= 80 else 4 if utterance.weight >= 60 else 3 if utterance.weight >= 40 else 2 if utterance.weight >= 24 else 1
        metadata = f'{t("source_key")} · {utterance.key} &nbsp; / &nbsp; {t("weight")} · {utterance.weight}'
        article = f'<article class="voice"><small class="voice-meta">{metadata}</small><div class="voice-phrase voice-weight-{weight_class}">{html.escape(utterance.text(language))}</div><div class="voice-versions">{"".join(variants)}</div><button disabled>{t("improve_translation")}</button><small>{t("proposals_closed")}</small></article>'
        text_column, record_column, translation_column = st.columns([12, 1, 1], vertical_alignment="top")
        with text_column:
            st.markdown(article, unsafe_allow_html=True)
        with record_column:
            if utterance.weight >= 30:
                if st.button("🎙", key=f"record-voice-{utterance.key}", help=t("record_voice")):
                    record_event(st.session_state, "event_recording_opened", utterance.key)
                    voice_recording_dialog(utterance)
        with translation_column:
            if st.button("+", key=f"add-translation-{utterance.key}", help=t("add_translation")):
                record_event(st.session_state, "event_translation_opened", utterance.key)
                translation_proposal_dialog(utterance)
    st.markdown('</main>', unsafe_allow_html=True)


repo, registry_mode = registry()
database_status = inspect_registry(repo, registry_mode)
player_registry_status = (
    "available" if registry_mode == "notion" else "unavailable"
)
capability_resolution = resolve_capability_player(repo, player_registry_status)
capability_player = capability_resolution.player
invitation_resolution = resolve_entry_invitation(repo, player_registry_status)
entry_invitation = (
    invitation_resolution.invitation
    if invitation_resolution.status == "resolved" else None
)
if capability_player is not None:
    record_event_once(
        st.session_state,
        f"capability-player-entered-{capability_player['player_id']}",
        "event_player_entered",
        str(capability_player["player_id"]),
        str((capability_player.get("metadata") or {}).get("node_stage") or ""),
    )
if capability_resolution.status == "registry_unavailable":
    st.error("PLAYER REGISTRY UNAVAILABLE · CAPABILITY NOT CHECKED")
elif capability_resolution.status == "registry_degraded":
    st.error("PLAYER REGISTRY DEGRADED · CAPABILITY NOT CHECKED")
elif capability_resolution.status == "malformed":
    st.error("CAPABILITY MALFORMED · NO PLAYER RESOLVED")
elif capability_resolution.status == "unknown":
    st.error("CAPABILITY INVALID OR EXPIRED · NO PLAYER RESOLVED")
elif capability_resolution.status == "revoked":
    st.error("CAPABILITY REVOKED · EDITING DISABLED")
elif capability_resolution.status == "integrity_error":
    st.error(
        "CAPABILITY OWNERSHIP CONFLICT · "
        f"{capability_resolution.matches} PLAYERS RESOLVED · EDITING DISABLED"
    )
if invitation_resolution.status == "registry_unavailable":
    st.error("INVITATION REGISTRY UNAVAILABLE · INVITE NOT CHECKED")
elif invitation_resolution.status == "registry_degraded":
    st.error("INVITATION REGISTRY DEGRADED · INVITE NOT CHECKED")
elif invitation_resolution.status == "malformed":
    st.error("INVITATION CODE MALFORMED")
elif invitation_resolution.status == "unknown":
    st.error("INVITATION UNKNOWN")
elif invitation_resolution.status == "consumed":
    st.error("INVITATION ALREADY CONSUMED")
elif invitation_resolution.status == "revoked":
    st.error("INVITATION REVOKED")
elif invitation_resolution.status == "integrity_error":
    st.error(
        "INVITATION CODE CONFLICT · "
        f"{invitation_resolution.matches} RECORDS FOUND"
    )
completed_population = st.session_state.get("completed-node-population")
saved_population = st.session_state.get("saved-node-population")
if saved_population:
    st.success(
        f"NODE SAVED · {saved_population['name']} · POPULATION CONTINUES · "
        "MISSING: " + ", ".join(item.upper() for item in saved_population["missing"])
    )
if completed_population:
    st.success(f"NODE READY · {completed_population['name']} · NETWORK UPDATED")
    st.markdown("**NEXT / PRIVATE UPLOAD**")
    code = str(completed_population.get("code") or "").strip()
    code_instruction = f" with recognition code **{code}**" if code else ""
    st.write(
        "Contact the person who invited you"
        f"{code_instruction} to receive the separate private upload route. "
        "That route encrypts material before storage; do not place private files in public URL fields."
    )
current_view = st.session_state.get("takeover_view") or str(st.query_params.get("view", "network"))
if str(st.query_params.get("k", "") or "").strip():
    current_view = "network"
if current_view not in {"network", "timeline", "necessities", "resources", "order-art", "voices"}:
    current_view = "network"
render_nav(current_view)
render_sidebar(current_view, registry_mode, database_status)
if current_view == "network":
    render_network(
        repo, registry_mode, database_status, capability_player, entry_invitation
    )
elif current_view == "timeline":
    render_timeline()
elif current_view == "necessities":
    render_necessities(repo)
elif current_view == "resources":
    render_resources(repo)
elif current_view == "order-art":
    render_order_art()
else:
    render_voices()
explicit_dialog = any(
    str(st.query_params.get(key, "") or "").strip()
    for key in ("node", "relation", "state", "door")
)
if capability_player is not None and not explicit_dialog:
    owned_node_dialog(repo, capability_player)
