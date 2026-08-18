"""TAKE OVER — Milestone 1 Streamlit scaffold."""

from __future__ import annotations

import os
from pathlib import Path
import re
import html

import streamlit as st
import streamlit.components.v1 as components

from takeover.graph import build_graph_html
from takeover.i18n import LANGUAGES, UTTERANCES, VOICE_LANGUAGES, translate, translator
from takeover.models import ENTITY_TYPES, STAGES, Entity
from takeover.registry import SessionRegistry
from takeover.style import CSS
from takeover.timeline import build_timeline_figure, load_trajectory


ROOT = Path(__file__).resolve().parent
TRAJECTORY = ROOT / "config" / "takeover_trajectory.yaml"

language = st.session_state.get("takeover_language", "en")
if language not in LANGUAGES:
    language = "en"
translation = translator(language)
_ = translation.gettext
p_ = lambda context, message: translate(translation, message, context)

st.set_page_config(page_title=p_("project name", "TAKE OVER"), page_icon="+", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)


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


@st.cache_resource
def _notion_registry(token: str):
    from takeover.notion import NotionRegistry
    return NotionRegistry(token)


def registry():
    token = _notion_token_value()
    if token:
        return _notion_registry(token), "notion"
    return SessionRegistry(st.session_state), "session"


def switch_view(view: str) -> None:
    st.session_state["takeover_view"] = view


@st.dialog(_("ACCESS DOOR"), width="large")
def access_door() -> None:
    st.caption(_("A PROJECT IN FORMATION"))
    st.markdown(_("The door opens onto what exists now. Other routes remain visible, but unopened."))
    st.markdown(f'<div class="door-option">{_("FOLLOW THE TRAJECTORY")}</div>', unsafe_allow_html=True)
    st.button(_("Open timeline →"), use_container_width=True, on_click=switch_view, args=("timeline",))
    st.markdown(f'<div class="door-option">{_("SEE WHAT IS NEEDED")}</div>', unsafe_allow_html=True)
    st.button(_("Open necessities →"), use_container_width=True, on_click=switch_view, args=("necessities",))
    st.markdown(f'<div class="door-option door-dormant">{_("CONTRIBUTE — UNOPENED")}</div>', unsafe_allow_html=True)
    st.button(_("This door is not active yet"), disabled=True, use_container_width=True)
    st.markdown(f'<div class="door-option door-dormant">{_("EXPLORE — DORMANT")}</div>', unsafe_allow_html=True)


@st.dialog(_("NODE"), width="large")
def node_dialog(entity: Entity) -> None:
    st.markdown(f'<div class="node-kind">{entity.type}</div>', unsafe_allow_html=True)
    st.header(entity.title)
    if entity.label:
        st.write(entity.label)
    st.caption(f'{_("STAGE")} · {entity.stage.upper()}   /   {_("STATUS")} · {entity.status.upper()}')
    if entity.source:
        st.write(entity.source)
    if entity.metadata:
        for key, value in entity.metadata.items():
            st.write(f"{key}: {value}")
    st.caption(f'{_("REGISTRY ID")} · {entity.id}')


def render_nav(current: str) -> None:
    st.markdown(f'<div class="takeover-brand">{p_("project name", "TAKE OVER")}</div>', unsafe_allow_html=True)
    with st.container(key="top-nav"):
        columns = st.columns([1, 1, 1, 1, 4])
        for column, label, key in zip(columns, (p_("navigation", "NETWORK"), p_("navigation", "TIMELINE"), p_("navigation", "NECESSITIES"), p_("page title", "VOICES")), ("network", "timeline", "necessities", "voices")):
            with column:
                st.button(label, key=f"nav-{key}", disabled=current == key, on_click=switch_view, args=(key,))


def render_sidebar(current: str, mode: str) -> None:
    with st.sidebar:
        st.title(p_("project name", "TAKE OVER"))
        st.caption(_("PROJECT NAVIGATION"))
        for label, key in (
            (p_("navigation", "NETWORK"), "network"),
            (p_("navigation", "TIMELINE"), "timeline"),
            (p_("navigation", "NECESSITIES"), "necessities"),
            (p_("page title", "VOICES"), "voices"),
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
        st.caption(f'{_("REGISTRY")} · {mode.upper()}')
        st.caption(_("DEVELOPMENT INTERFACE"))


def render_network(repo, mode: str) -> None:
    entities = repo.list_entities()
    relations = repo.list_relations()
    left, right = st.columns([0.8, 1.55], gap="large")
    with left:
        st.markdown('<div class="takeover-copy">', unsafe_allow_html=True)
        st.title(p_("project name", "TAKE OVER"))
        st.markdown(f'<div class="takeover-kicker">{_("A COMMUNITY IN PROGRESS")}</div>', unsafe_allow_html=True)
        manifesto = "<br>".join(map(_, ("We start from what remains.", "We open doors.", "We listen. We respond.", "We build what comes next — together.")))
        manifesto += "<br><br>" + "<br>".join(map(_, ("This is a live project.", "It grows with every connection.")))
        st.markdown(f'<div class="takeover-manifesto">{manifesto}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="takeover-entry"><strong>{_("ENTER THE NETWORK")}</strong><span>{_("Open the central node to begin.")}<br>{_("The system grows from explicit relations.")}</span></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        components.html(build_graph_html(entities, relations, p_("network action", "START HERE"), p_("network invitation", "YOU?"), _("Bring your voice, your image, your practice."), p_("empty network state", "nothing?")), height=610, scrolling=False)
    if str(st.query_params.get("door", "") or "") == "access":
        access_door()
    requested = str(st.query_params.get("node", "") or "")
    selected = next((item for item in entities if item.id == requested), None)
    if selected:
        node_dialog(selected)
    if os.getenv("TAKEOVER_ADMIN_MODE", "").strip() == "1":
        render_admin(repo, mode)


def render_admin(repo, mode: str) -> None:
    with st.expander(_("Developer controls · Add node"), expanded=False):
        st.caption(_("Local/admin validation only. This surface is absent unless TAKEOVER_ADMIN_MODE=1."))
        with st.form("add-node-form", clear_on_submit=True):
            kind = st.selectbox(_("Entity type"), ENTITY_TYPES)
            title = st.text_input(_("Name / title"))
            entity_id = st.text_input(_("ID"), placeholder="ave")
            label = st.text_input(_("Label"), placeholder="artist")
            stage = st.selectbox(_("Stage"), STAGES)
            source = st.text_input(_("Image or audio URL"), placeholder="https://…")
            submitted = st.form_submit_button(_("Add entity"), use_container_width=True)
        if submitted:
            clean_id = re.sub(r"[^a-z0-9_-]+", "-", entity_id.strip().lower()).strip("-")
            try:
                repo.add_entity(Entity(clean_id, kind, title.strip(), label.strip(), stage, "active", source.strip()))
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success(_("Added %(title)s to the %(mode)s registry.") % {"title": title, "mode": mode})
                st.rerun()


def render_timeline() -> None:
    st.markdown(f'<div class="section-head">{p_("navigation", "TIMELINE")} · {p_("project stage", "APPLICATION")}</div>', unsafe_allow_html=True)
    payload = load_trajectory(TRAJECTORY)
    plan = payload["plan"]
    st.caption(str(plan.get("description") or _("A trajectory toward the opening of TAKE OVER.")))
    st.plotly_chart(build_timeline_figure(payload), use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
    st.caption(_("READ-ONLY M1 VIEW · YAML REMAINS THE TIMELINE SOURCE"))


def render_necessities(repo) -> None:
    st.markdown(f'<div class="section-head">{_("WHAT THE PROJECT NEEDS NOW")}</div>', unsafe_allow_html=True)
    st.caption(_("Need → stage → state. This is not a resources directory."))
    necessity_labels = {"abstract": "Abstract", "material": "Material", "initial_kernel": "Initial kernel", "photographs": "Photographs", "voices_sound": "Voices + sound", "translation": "Translation"}
    status_labels = {"in_progress": "IN PROGRESS", "collecting": "COLLECTING", "found": "FOUND", "agreed": "AGREED", "open": "OPEN"}
    necessities = repo.list_necessities()
    for item in sorted(necessities, key=lambda value: (value.stage, value.title)):
        st.markdown(
            f'<div class="necessity"><strong>{p_("necessity name", necessity_labels.get(item.title, item.title))}</strong><span class="stage">{p_("project stage", item.stage.upper())}</span><span class="status">{p_("necessity status", status_labels.get(item.status, item.status.upper()))}</span></div>',
            unsafe_allow_html=True,
        )
    if not necessities:
        st.info(_("No necessities have been activated yet."))


def set_language(language: str) -> None:
    st.session_state["takeover_language"] = language


def render_voices() -> None:
    catalogues = {code: translator(code) for code in VOICE_LANGUAGES}
    st.markdown('<main class="voices">', unsafe_allow_html=True)
    st.markdown(f'<div class="voices-head"><h1>{p_("page title", "VOICES")}</h1><p>{_("Every translatable utterance currently spoken by TAKE OVER, arranged by weight.")}</p></div>', unsafe_allow_html=True)
    for index, utterance in enumerate(UTTERANCES):
        variants = []
        for code in VOICE_LANGUAGES:
            rendered = translate(catalogues[code], utterance.message, utterance.context)
            variants.append(f'<span><b>{code.upper()}</b>{html.escape(rendered)}</span>')
        weight_class = 5 if utterance.weight >= 80 else 4 if utterance.weight >= 60 else 3 if utterance.weight >= 40 else 2 if utterance.weight >= 24 else 1
        st.markdown(f'<article class="voice"><div class="voice-phrase voice-weight-{weight_class}">{html.escape(translate(translation, utterance.message, utterance.context))}</div><div class="voice-versions">{"".join(variants)}</div><button disabled>{p_("translation action", "IMPROVE THIS TRANSLATION")}</button><small>{_("Proposals are not open yet.")}</small></article>', unsafe_allow_html=True)
    st.markdown('</main>', unsafe_allow_html=True)


repo, registry_mode = registry()
current_view = st.session_state.get("takeover_view") or str(st.query_params.get("view", "network"))
if current_view not in {"network", "timeline", "necessities", "voices"}:
    current_view = "network"
render_nav(current_view)
render_sidebar(current_view, registry_mode)
if current_view == "network":
    render_network(repo, registry_mode)
elif current_view == "timeline":
    render_timeline()
elif current_view == "necessities":
    render_necessities(repo)
else:
    render_voices()
