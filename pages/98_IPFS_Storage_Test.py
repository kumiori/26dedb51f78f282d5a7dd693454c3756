"""Minimal Filebase S3 → IPFS → CID test surface."""

from __future__ import annotations

import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
import streamlit as st


st.set_page_config(page_title="TAKE OVER · Drop Test", page_icon="+", layout="centered")
st.title("DROP / TEST")
st.caption("Filebase → IPFS → CID")

try:
    cfg = st.secrets["filebase"]
    s3 = boto3.client(
        "s3",
        endpoint_url=cfg["endpoint"],
        aws_access_key_id=cfg["access_key"],
        aws_secret_access_key=cfg["secret_key"],
        region_name=cfg.get("region", "auto"),
        config=Config(
            signature_version="s3v4"
            if cfg.get("signature_version", "v4") == "v4"
            else cfg["signature_version"]
        ),
    )
except (KeyError, TypeError):
    st.error("FILEBASE IS NOT CONFIGURED IN BACKEND SECRETS")
    st.stop()

try:
    configured_bucket = str(cfg.get("bucket", "") or "").strip()
    bucket_names = [configured_bucket] if configured_bucket else [
        item["Name"] for item in s3.list_buckets().get("Buckets", [])
    ]
except (BotoCoreError, ClientError) as exc:
    st.error(f"FILEBASE CONNECTION FAILED · {exc}")
    st.stop()

if not bucket_names:
    st.warning("NO ACCESSIBLE BUCKETS · create an IPFS bucket in Filebase first")
    st.stop()

bucket = bucket_names[0] if len(bucket_names) == 1 else st.selectbox("BUCKET", bucket_names)

try:
    response = s3.list_objects_v2(Bucket=bucket)
    objects = response.get("Contents", [])
except (BotoCoreError, ClientError) as exc:
    st.error(f"BUCKET COULD NOT BE READ · {exc}")
    st.stop()

object_count, weight = st.columns(2)
object_count.metric("OBJECTS", len(objects))
total_bytes = sum(int(item.get("Size", 0)) for item in objects)
weight.metric("WEIGHT", f"{total_bytes / 1024 / 1024:.2f} MB" if total_bytes else "0 B")

if result := st.session_state.pop("filebase_upload_result", None):
    st.success("RECEIVED")
    st.write(f"**FILE**  {result['filename']}")
    st.write(f"**WEIGHT**  {result['bytes']:,} bytes")
    st.write(f"**CID**  `{result['cid'] or 'CID pending / inspect metadata'}`")
    st.write(f"**OBJECT**  `{result['key']}`")

uploaded = st.file_uploader("Drop something")
if uploaded is not None:
    data = uploaded.getvalue()
    nbytes = len(data)
    if st.button("ENTER TAKE OVER", use_container_width=True):
        key = f"test/{uuid.uuid4()}-{uploaded.name}"
        try:
            with st.spinner("Uploading..."):
                s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data,
                    ContentType=uploaded.type or "application/octet-stream",
                )
                meta = s3.head_object(Bucket=bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            st.error(f"UPLOAD FAILED · {exc}")
        else:
            cid = (
                meta.get("Metadata", {}).get("cid")
                or meta.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amz-meta-cid")
            )
            st.session_state["filebase_upload_result"] = {
                "filename": uploaded.name,
                "bytes": nbytes,
                "cid": cid,
                "key": key,
            }
            st.rerun()

st.caption("TODAY: DROP → STORE → CID → WEIGH")
