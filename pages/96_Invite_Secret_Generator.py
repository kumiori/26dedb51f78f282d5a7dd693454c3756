"""Local operator page for generating participant invitation secrets."""

from pathlib import Path

import streamlit as st

from takeover.invite_secrets import append_invite, batch_toml, generate_invite, invite_toml


ROOT = Path(__file__).resolve().parents[1]
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"

st.set_page_config(page_title="TAKE OVER · Invite secrets", page_icon="🔑", layout="centered")
st.title("INVITE SECRET GENERATOR")
st.warning("LOCAL OPERATOR TOOL · the generated drop token opens a participant link. Do not share this screen or commit the secrets file.")

name = st.text_input("Participant name", placeholder="Ave")

generate_column, append_column = st.columns(2)
generate_clicked = generate_column.button("GENERATE", disabled=not name.strip(), use_container_width=True)
append_clicked = append_column.button("GENERATE + APPEND", type="primary", disabled=not name.strip(), use_container_width=True)

if generate_clicked or append_clicked:
    try:
        identity, values = generate_invite(name)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.session_state["generated-invite"] = {"identity": identity, "values": values}
        if append_clicked:
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
    st.code(f"?view=resources&k={values['drop_token']}", language="text")
    st.caption("SHORT OPAQUE TOKEN · EXACT-MATCH ROUTING · NO ACCESS KEY · NO CAPABILITY")

    confirm = st.checkbox("I understand this writes credentials to the local ignored secrets file.")
    if st.button("SAVE TO .streamlit/secrets.toml", disabled=not confirm, use_container_width=True):
        try:
            append_invite(SECRETS_PATH, identity, values)
        except (OSError, ValueError) as exc:
            st.error(str(exc))
        else:
            st.success("SAVED LOCALLY · RESTART STREAMLIT TO RELOAD SECRETS")

batch = st.session_state.get("generated-invite-batch", [])
if batch:
    st.divider()
    st.subheader(f"BATCH · {len(batch)}")
    batch_rows = [(item["identity"], item["values"]) for item in batch]
    st.caption("COPY ALL SECRETS")
    st.code(batch_toml(batch_rows), language="toml")
    st.caption("COPY ALL DROP LINKS")
    st.code("\n".join(f"?view=resources&k={values['drop_token']}" for _identity, values in batch_rows), language="text")
    if st.button("CLEAR BATCH", use_container_width=True):
        st.session_state["generated-invite-batch"] = []
        st.rerun()

st.caption(f"TARGET · {SECRETS_PATH.relative_to(ROOT)} · GIT-IGNORED")
