"""Single-link encrypted drop surface for the participant storage test."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
import streamlit as st

from takeover.browser_encrypt import encrypted_drop
from takeover.encrypted_storage import EncryptedContribution, EncryptedRegistry
from takeover.identity import resolve_drop_token


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = Path(os.getenv("TAKEOVER_ENCRYPTED_REGISTRY", ROOT / "data" / "encrypted_storage_v1.json"))
registry = EncryptedRegistry(REGISTRY_PATH)

st.set_page_config(page_title="TAKE OVER · Drop", page_icon="+", layout="centered")
st.title("DROP / TEST")
st.caption("PARTICIPANT LINK → DROP → ENCRYPT → STORE → WEIGH")

try:
    cfg = st.secrets["filebase"]
    identities = {name: dict(value) for name, value in st.secrets["takeover_identities"].items()}
    signature = "s3v4" if cfg.get("signature_version", "v4") == "v4" else cfg["signature_version"]
    s3 = boto3.client(
        "s3",
        endpoint_url=cfg["endpoint"],
        aws_access_key_id=cfg["access_key"],
        aws_secret_access_key=cfg["secret_key"],
        region_name=cfg.get("region", "auto"),
        config=Config(signature_version=signature),
    )
    bucket = cfg["bucket"]
except (KeyError, TypeError):
    st.error("STORAGE IS NOT CONFIGURED")
    st.stop()

try:
    response = s3.list_objects_v2(Bucket=bucket)
    bucket_objects = response.get("Contents", [])
except (BotoCoreError, ClientError) as exc:
    st.error(f"BUCKET COULD NOT BE READ · {exc}")
    st.stop()

object_count, weight = st.columns(2)
object_count.metric("OBJECTS", len(bucket_objects))
encrypted_weight = sum(int(item.get("Size", 0)) for item in bucket_objects)
weight.metric("BUCKET WEIGHT", f"{encrypted_weight / 1024 / 1024:.2f} MB" if encrypted_weight else "0 B")
st.caption("PLAINTEXT · UNAVAILABLE")


@st.dialog("DROP / PRIVATE", width="large")
def private_drop(participant: str) -> None:
    st.caption(f"FOR · {participant}")
    contribution_id = str(uuid.uuid4())
    namespace = hashlib.sha256(identities[participant]["capability"].encode()).hexdigest()[:16]
    object_key = f"private/{participant}/{namespace}/{contribution_id}.enc"
    try:
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": object_key, "ContentType": "application/octet-stream"},
            ExpiresIn=900,
        )
    except (BotoCoreError, ClientError) as exc:
        st.error(f"DROP COULD NOT BE PREPARED · {exc}")
        return

    result = encrypted_drop(
        data={
            "upload_url": upload_url,
            "object_key": object_key,
            "contribution_id": contribution_id,
            "participant": participant,
            "identity_key": identities[participant]["access_key"],
        },
        default={"uploaded": None},
        key=f"private-drop-{participant}",
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
        st.error(f"DROP COULD NOT BE VERIFIED · {exc}")
        return

    cid = (
        meta.get("Metadata", {}).get("cid")
        or meta.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amz-meta-cid")
    )
    row = registry.add(EncryptedContribution(
        id=uploaded["id"],
        contributor_id=participant,
        created_at=datetime.now(timezone.utc).isoformat(),
        object={
            "cid": cid,
            "key": uploaded["key"],
            "filename": uploaded["filename"],
            "encrypted_bytes": int(meta.get("ContentLength", uploaded["encrypted_bytes"])),
            "original_bytes": int(uploaded["original_bytes"]),
            "mime_type": "application/octet-stream",
            "original_mime_type": uploaded["original_mime_type"],
        },
        crypto={
            "algorithm": "AES-256-GCM",
            "version": 1,
            "iv": uploaded["iv"],
            "kdf": uploaded["kdf"],
            "salt": uploaded["salt"],
            "wrap_iv": uploaded["wrap_iv"],
            "wrapped_key": uploaded["wrapped_key"],
            "key_reference": uploaded["key_reference"],
        },
    ))
    st.success("RECEIVED")
    st.write(f"**FILE**  {row.object['filename']}")
    st.write(f"**WEIGHT**  {row.object['encrypted_bytes']:,} bytes")
    st.write(f"**CID**  `{row.object['cid'] or 'CID pending'}`")


drop_token = str(st.query_params.get("k", "") or "")
participant = resolve_drop_token(drop_token, identities)
if participant:
    private_drop(participant)
elif drop_token:
    st.warning("THIS DROP LINK IS NOT ACTIVE")
else:
    st.info("OPEN A PARTICIPANT DROP LINK TO SEND A FILE")

st.caption("STORAGE TEST · ONE PARTICIPANT LINK · ONE DROP · NO SHARING")
