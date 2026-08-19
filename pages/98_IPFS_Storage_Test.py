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
import plotly.graph_objects as go
import streamlit as st

from takeover.browser_encrypt import encrypted_drop
from takeover.encrypted_storage import EncryptedContribution, EncryptedRegistry
from takeover.identity import resolve_drop_token
from takeover.storage_timeline import storage_timeline


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = Path(
    os.getenv(
        "TAKEOVER_ENCRYPTED_REGISTRY", ROOT / "data" / "encrypted_storage_v1.json"
    )
)
registry = EncryptedRegistry(REGISTRY_PATH)

st.set_page_config(page_title="TAKE OVER · Drop", page_icon="+", layout="centered")
st.title("DROP / TEST")
st.caption("PARTICIPANT LINK → DROP → ENCRYPT → STORE → WEIGH")

try:
    cfg = st.secrets["filebase"]
    identities = {
        name: dict(value) for name, value in st.secrets["takeover_identities"].items()
    }
    signature = (
        "s3v4"
        if cfg.get("signature_version", "v4") == "v4"
        else cfg["signature_version"]
    )
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
# Direct browser PUTs to a presigned Filebase URL require bucket CORS.
# This permissive origin is only for the current storage test. Once the
# deployed origin is stable, replace "*" with that exact app origin.
TEST_CORS = {
    "CORSRules": [
        {
            "AllowedMethods": ["PUT", "GET", "HEAD"],
            "AllowedOrigins": ["*"],
            "AllowedHeaders": ["*"],
            "ExposeHeaders": ["ETag", "x-amz-meta-cid"],
            "MaxAgeSeconds": 3000,
        }
    ]
}

try:
    s3.put_bucket_cors(Bucket=bucket, CORSConfiguration=TEST_CORS)
except (BotoCoreError, ClientError) as exc:
    st.warning(f"BUCKET CORS COULD NOT BE CONFIGURED · {exc}")
try:
    response = s3.list_objects_v2(Bucket=bucket)
    bucket_objects = response.get("Contents", [])
except (BotoCoreError, ClientError) as exc:
    st.error(f"BUCKET COULD NOT BE READ · {exc}")
    st.stop()

object_count, weight = st.columns(2)
object_count.metric("OBJECTS", len(bucket_objects))
encrypted_weight = sum(int(item.get("Size", 0)) for item in bucket_objects)
weight.metric(
    "BUCKET WEIGHT",
    f"{encrypted_weight / 1024 / 1024:.2f} MB" if encrypted_weight else "0 B",
)
st.caption("PLAINTEXT · UNAVAILABLE")

timeline = storage_timeline(bucket_objects)
figure = go.Figure()
figure.add_trace(go.Scatter(
    x=timeline["horizon_times"],
    y=[value / 1024 / 1024 for value in timeline["horizon_bytes"]],
    mode="lines",
    line={"color": "#aaa6a0", "width": 2, "dash": "dot"},
    name="DISPLAY HORIZON",
    hovertemplate="Current measured weight held constant<br>%{y:.3f} MB<extra></extra>",
))
figure.add_trace(go.Scatter(
    x=timeline["actual_times"],
    y=[value / 1024 / 1024 for value in timeline["actual_bytes"]],
    mode="lines+markers",
    line={"color": "#111111", "width": 3, "shape": "spline", "smoothing": 1.0},
    marker={"size": 12, "color": "#f04a24", "line": {"color": "#111111", "width": 1.5}},
    name="OBSERVED",
    cliponaxis=False,
    hovertemplate="%{x|%d %b %Y · %H:%M}<br>%{y:.3f} MB<extra></extra>",
))
figure.add_vline(x=timeline["now"].timestamp() * 1000, line_width=1, line_dash="dash", line_color="#777168")
figure.add_annotation(x=timeline["now"], y=1, yref="paper", text="NOW", showarrow=False, xanchor="left", yanchor="bottom")
figure.update_layout(
    title="IPFS STORAGE / TIME",
    xaxis={"title": "TIME", "range": [timeline["window_start"], timeline["window_end"]], "showgrid": False},
    yaxis={"title": "ENCRYPTED WEIGHT / MB", "rangemode": "tozero", "gridcolor": "rgba(0,0,0,.09)"},
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "x": 0},
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hovermode="x unified",
)
st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
st.caption("OBSERVED FROM DAY −2 · TWO-MONTH DISPLAY HORIZON · DOTTED LINE HOLDS TODAY'S MEASURED WEIGHT CONSTANT")
if timeline["missing_timestamps"]:
    st.warning(f"{timeline['missing_timestamps']} BUCKET OBJECT(S) HAVE NO LAST-MODIFIED TIMESTAMP AND ARE EXCLUDED FROM THE TIME SERIES")


@st.dialog("DROP / PRIVATE", width="large")
def private_drop(participant: str) -> None:
    st.caption(f"FOR · {participant}")
    contribution_id = str(uuid.uuid4())
    namespace = hashlib.sha256(
        identities[participant]["capability"].encode()
    ).hexdigest()[:16]
    object_key = f"private/{participant}/{namespace}/{contribution_id}.enc"
    try:
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": object_key,
                "ContentType": "application/octet-stream",
            },
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
            "content_type": "application/octet-stream",
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
        and all(
            re.fullmatch(r"[A-Za-z0-9_-]+", str(uploaded.get(field, "")))
            for field in ("iv", "salt", "wrap_iv", "wrapped_key")
        )
    )
    if not valid:
        st.error("DROP METADATA FAILED VALIDATION")
        return

    try:
        meta = s3.head_object(Bucket=bucket, Key=uploaded["key"])
    except (BotoCoreError, ClientError) as exc:
        st.error(f"DROP COULD NOT BE VERIFIED · {exc}")
        return

    cid = meta.get("Metadata", {}).get("cid") or meta.get("ResponseMetadata", {}).get(
        "HTTPHeaders", {}
    ).get("x-amz-meta-cid")
    row = registry.add(
        EncryptedContribution(
            id=uploaded["id"],
            contributor_id=participant,
            created_at=datetime.now(timezone.utc).isoformat(),
            object={
                "cid": cid,
                "key": uploaded["key"],
                "filename": uploaded["filename"],
                "encrypted_bytes": int(
                    meta.get("ContentLength", uploaded["encrypted_bytes"])
                ),
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
        )
    )
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
