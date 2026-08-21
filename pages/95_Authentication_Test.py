"""Test surface for persona minting and authentication interactions."""

from datetime import datetime, timezone
import secrets

import streamlit as st

from takeover.persona_auth import ProvisionalPersonaStore, authenticate_persona, mint_persona
from takeover.style import CSS


st.set_page_config(page_title="TAKE OVER · Authentication test", page_icon="◉", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)
st.title("PERSONA / AUTHENTICATION TEST")
st.caption("TEST SURFACE · NO REMOTE DURABILITY CLAIMED")

store = ProvisionalPersonaStore(st.session_state)
nickname = st.text_input("Name / alias", placeholder="Optional")

if st.button("GENERATE PERSONA", type="primary", use_container_width=True):
    result = mint_persona(
        store,
        nickname=nickname,
        key_factory=lambda: secrets.token_hex(16),
        clock=lambda: datetime.now(timezone.utc),
    )
    st.session_state["active_persona_key"] = result.persona.access_key

active = store.get_persona(str(st.session_state.get("active_persona_key", "")))
if active:
    st.markdown("<div class='persona-kicker'>YOUR EMOJI PROJECTION</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='persona-emoji'>{active.emoji_suffix_4}</div>", unsafe_allow_html=True)
    st.caption("FOUR-SYMBOL DISCOVERY SUFFIX · NOT A CAPABILITY")
    with st.expander("FULL AUTHENTICATION MATERIAL"):
        st.code(active.access_key, language="text")
        st.write(active.emoji)
        st.caption("22-SYMBOL REVERSIBLE PROJECTION OF THE SAME 128-BIT VALUE")

st.divider()
st.subheader("RETURN")
raw_key = st.text_input("Access key or emoji suffix", type="password")
if st.button("AUTHENTICATE", disabled=not raw_key.strip(), use_container_width=True):
    result = authenticate_persona(store, raw_key, clock=lambda: datetime.now(timezone.utc))
    if result is None:
        st.error("KEY INVALID OR AMBIGUOUS")
    else:
        st.session_state["active_persona_key"] = result.persona.access_key
        st.success("PERSONA RECOGNISED")

st.divider()
st.markdown("**PROVISIONAL · SESSION-LOCAL**")
st.caption("PERSONA UPSERTS AND INTERACTIONS ARE VISIBLE HERE FOR TESTING. THEY ARE NOT YET WRITTEN TO THE TAKE OVER DATABASE.")
st.metric("PERSONAS", len(store.list_personas()))
st.metric("INTERACTIONS", len(store.list_interactions()))

with st.expander("WHAT THIS TEST COMPILES"):
    st.write("Persona: canonical key, nickname, full emoji projection, 4/6-symbol suffixes, authority, created and last-authenticated timestamps.")
    st.write("Interaction: unique id, kind, persona key, timestamp, authority and interface source.")
