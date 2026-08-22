"""Read-only database connectivity and graph-projection diagnostics."""

from __future__ import annotations

import os
from pathlib import Path
import hashlib
import json
import importlib.metadata

import streamlit as st

from takeover.database_status import inspect_factory_health, inspect_registry
from takeover.events import list_events
from takeover.registry import SessionRegistry


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "takeover_notion.json"


def notion_token() -> tuple[str, str]:
    token = os.getenv("NOTION_TOKEN", "").strip()
    if token:
        return token, "environment"
    try:
        token = str(st.secrets.get("NOTION_TOKEN", "") or "").strip()
        if not token:
            notion = st.secrets.get("notion", {})
            token = str(notion.get("token") or notion.get("api_key") or "").strip()
    except (KeyError, TypeError, AttributeError):
        token = ""
    return token, "streamlit secrets" if token else "none"


def storage_probe():
    try:
        cfg = st.secrets["filebase"]
        import boto3
        from botocore.config import Config

        client = boto3.client(
            "s3",
            endpoint_url=cfg["endpoint"],
            aws_access_key_id=cfg["access_key"],
            aws_secret_access_key=cfg["secret_key"],
            region_name=cfg.get("region", "auto"),
            config=Config(
                signature_version="s3v4",
                connect_timeout=2,
                read_timeout=2,
                retries={"max_attempts": 1},
            ),
        )
        client.list_objects_v2(Bucket=cfg["bucket"], MaxKeys=1)
        return True
    except (KeyError, TypeError, AttributeError):
        return None


def storage_configured() -> bool:
    try:
        cfg = st.secrets["filebase"]
        return all(str(cfg.get(key) or "").strip() for key in ("endpoint", "access_key", "secret_key", "bucket"))
    except (KeyError, TypeError, AttributeError):
        return False


st.set_page_config(page_title="TAKE OVER · Database Test", page_icon="+", layout="wide")
st.title("DATABASE TEST")
st.caption("READ ONLY · NO DATABASE ROWS, IDENTIFIERS OR SECRET VALUES ARE DISPLAYED")

token, configuration_source = notion_token()
if token:
    from takeover.notion import NotionRegistry

    repo = NotionRegistry(token, MANIFEST)
    mode = "notion"
else:
    repo = SessionRegistry(st.session_state)
    mode = "session"

result = inspect_registry(repo, mode)
st.markdown(
    f"**STATUS · {result.status.upper()}**  \n"
    f"AUTHORITY · {result.authority.upper()}  \n"
    f"ADAPTER · {result.mode.upper()}  \n"
    f"CONFIGURATION · {configuration_source.upper()}"
)
node_metric, relation_metric = st.columns(2)
node_metric.metric("NODES", result.entity_count)
relation_metric.metric("RELATIONS", result.relation_count)

if result.status == "empty":
    st.warning("THE SELECTED REGISTRY RETURNED NO PROJECTED GRAPH ROWS")
elif result.status == "error":
    st.error(f"DATABASE READ FAILED · {result.error_type}")
else:
    st.success("DATABASE READ COMPLETED")

if mode == "notion":
    manifest_payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_fingerprint = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()[:12]
    token_fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
    st.subheader("CONNECTION ISOLATION")
    st.caption(
        "SAFE CONFIGURATION FINGERPRINTS CAN BE COMPARED BETWEEN LOCAL AND DEPLOYED "
        "RUNTIMES. THEY ARE NOT TOKENS OR DATABASE IDENTIFIERS."
    )
    st.dataframe([
        {"check": "TOKEN PRESENT", "value": "yes"},
        {
            "check": "TOKEN FORMAT",
            "value": "recognised" if token.startswith(("ntn_", "secret_")) else "unexpected",
        },
        {"check": "TOKEN CONFIG FINGERPRINT", "value": token_fingerprint},
        {"check": "MANIFEST FINGERPRINT", "value": manifest_fingerprint},
        {"check": "MANIFEST SCHEMA", "value": str(manifest_payload.get("schema_version") or "missing")},
        {"check": "MANIFEST STATUS", "value": str(manifest_payload.get("status") or "missing")},
        {"check": "MANIFEST SOURCES", "value": str(len(manifest_payload.get("databases") or {}))},
        {"check": "NOTION API VERSION", "value": repo.API_VERSION},
        {"check": "NOTION CLIENT", "value": importlib.metadata.version("notion-client")},
    ], hide_index=True, width="stretch")
    st.markdown("**BOUNDARY PROBES**")
    st.dataframe(repo.connection_diagnostics(), hide_index=True, width="stretch")
    st.caption(
        "401 / TOKEN REJECTED → replace or re-save the deployed integration secret.  \n"
        "403 / INTEGRATION LACKS ACCESS → share the Takeover databases with that integration.  \n"
        "404 / SOURCE NOT SHARED OR MANIFEST MISMATCH → compare fingerprints, then share the "
        "databases or deploy the current manifest.  \n"
        "400 / REQUEST OR API CONTRACT REJECTED → check the deployed notion-client version and API version."
    )

source_diagnostics = getattr(repo, "source_diagnostics", None)
if callable(source_diagnostics):
    st.subheader("SOURCE CHECKS")
    st.dataframe(source_diagnostics(), hide_index=True, width="stretch")
else:
    st.info("NO AUTHORITATIVE DATABASE ADAPTER IS CONFIGURED IN THIS RUNTIME")

st.divider()
st.header("FACTORY HEALTH")
configured_probe = storage_probe if storage_configured() else None
if mode == "notion":
    factory = inspect_factory_health(repo, mode, storage_probe=configured_probe)
    health_columns = st.columns(3)
    health_columns[0].metric("NOTION", factory.notion.upper())
    health_columns[1].metric("STORAGE", factory.storage.upper())
    health_columns[2].metric("SCHEMA", factory.schema.upper())
    if all(value in {"reachable", "compatible"} for value in (factory.notion, factory.storage, factory.schema)):
        st.success("FACTORY HEALTHY")
    else:
        st.warning("FACTORY REQUIRES ATTENTION")
    st.subheader("RECOVERY")
    recovery = st.columns(3)
    recovery[0].metric("DUPLICATE PERSON IDs", factory.duplicate_person_ids)
    recovery[1].metric("DUPLICATE CAPABILITY OWNERS", factory.duplicate_capability_owners)
    recovery[2].metric("DUPLICATE INVITATION REQUESTS", factory.duplicate_invitation_requests)
else:
    st.info("AUTHORITATIVE FACTORY HEALTH REQUIRES THE NOTION ADAPTER")

st.subheader("EVENT LOG")
events = list_events(st.session_state)
if events:
    st.dataframe(events, hide_index=True, width="stretch")
else:
    st.caption("NO FACTORY EVENTS IN THIS SESSION")
