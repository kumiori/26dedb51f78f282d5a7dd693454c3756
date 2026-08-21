"""Operator page for generating copyable participant credentials."""

import streamlit as st

from takeover.invite_secrets import batch_toml, generate_invite, invite_toml

st.set_page_config(page_title="TAKE OVER · Invite secrets", page_icon="🔑", layout="centered")
st.title("INVITE SECRET GENERATOR")
st.warning("OPERATOR TOOL · SESSION ONLY · copy the output into the app's runtime configuration. This page changes no files or deployment settings.")

name = st.text_input("Participant name", placeholder="Ave")

generate_column, batch_column = st.columns(2)
generate_clicked = generate_column.button("GENERATE", disabled=not name.strip(), use_container_width=True)
batch_clicked = batch_column.button("GENERATE + ADD TO BATCH", type="primary", disabled=not name.strip(), use_container_width=True)

if generate_clicked or batch_clicked:
    try:
        identity, values = generate_invite(name)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.session_state["generated-invite"] = {"identity": identity, "values": values}
        if batch_clicked:
            batch = st.session_state.setdefault("generated-invite-batch", [])
            if any(item["identity"] == identity for item in batch):
                st.error(f"{identity} is already in this batch. Use a different participant name or clear the batch.")
            else:
                batch.append({"identity": identity, "values": values})

generated = st.session_state.get("generated-invite")
if generated:
    identity = generated["identity"]
    values = generated["values"]
    st.subheader(identity)
    st.code(invite_toml(identity, values), language="toml")
    st.caption("PRIVATE DROP")
    st.code(f"?view=resources&k={values['drop_token']}", language="text")
    st.caption("MODIFY OWN PROFILE · KEEP THIS CAPABILITY PRIVATE")
    st.code(f"?c={values['capability']}", language="text")

batch = st.session_state.get("generated-invite-batch", [])
if batch:
    st.divider()
    st.subheader(f"BATCH · {len(batch)}")
    batch_rows = [(item["identity"], item["values"]) for item in batch]
    st.caption("COPY ALL SECRETS")
    st.code(batch_toml(batch_rows), language="toml")
    st.caption("COPY ALL DROP LINKS")
    st.code("\n".join(f"?view=resources&k={values['drop_token']}" for _identity, values in batch_rows), language="text")
    st.caption("COPY ALL PROFILE CAPABILITY LINKS")
    st.code("\n".join(f"?c={values['capability']}" for _identity, values in batch_rows), language="text")
    if st.button("CLEAR BATCH", use_container_width=True):
        st.session_state["generated-invite-batch"] = []
        st.rerun()

st.caption("OUTPUT · SESSION ONLY · MANUALLY ADD THE TOML TO THE APP'S RUNTIME CONFIGURATION")
