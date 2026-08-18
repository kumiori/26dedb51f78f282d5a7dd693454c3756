"""TAKE OVER — Milestone 1 Streamlit scaffold."""

from __future__ import annotations

import os
from pathlib import Path
import re
import html

import streamlit as st
import streamlit.components.v1 as components

from takeover.graph import build_graph_html
from takeover.i18n import LANGUAGES, UTTERANCES, VOICE_LANGUAGES, translate
from takeover.models import ENTITY_TYPES, STAGES, Entity
from takeover.registry import SessionRegistry
from takeover.style import CSS
from takeover.timeline import build_timeline_figure, load_trajectory


ROOT = Path(__file__).resolve().parent
TRAJECTORY = ROOT / "config" / "takeover_trajectory.yaml"

language = st.session_state.get("takeover_language", "en")
if language not in LANGUAGES:
    language = "en"
t = lambda key: translate(key, language)

st.set_page_config(page_title=t("project_name"), page_icon="+", layout="wide", initial_sidebar_state="expanded")
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


@st.dialog(t("access_door"), width="large")
def access_door() -> None:
    st.caption(t("project_formation"))
    st.markdown(t("door_intro"))
    st.markdown(f'<div class="door-option">{t("follow_trajectory")}</div>', unsafe_allow_html=True)
    st.button(t("open_timeline"), use_container_width=True, on_click=switch_view, args=("timeline",))
    st.markdown(f'<div class="door-option">{t("see_needed")}</div>', unsafe_allow_html=True)
    st.button(t("open_necessities"), use_container_width=True, on_click=switch_view, args=("necessities",))
    st.markdown(f'<div class="door-option door-dormant">{t("contribute_unopened")}</div>', unsafe_allow_html=True)
    st.button(t("door_inactive"), disabled=True, use_container_width=True)
    st.markdown(f'<div class="door-option door-dormant">{t("explore_dormant")}</div>', unsafe_allow_html=True)


@st.dialog(t("node"), width="large")
def node_dialog(entity: Entity) -> None:
    st.markdown(f'<div class="node-kind">{entity.type}</div>', unsafe_allow_html=True)
    st.header(entity.title)
    if entity.label:
        st.write(entity.label)
    st.caption(f'{t("stage")} · {entity.stage.upper()}   /   {t("status")} · {entity.status.upper()}')
    if entity.source:
        st.write(entity.source)
    if entity.metadata:
        for key, value in entity.metadata.items():
            st.write(f"{key}: {value}")
    st.caption(f'{t("registry_id")} · {entity.id}')


def render_nav(current: str) -> None:
    st.markdown(f'<div class="takeover-brand">{t("project_name")}</div>', unsafe_allow_html=True)
    with st.container(key="top-nav"):
        columns = st.columns([1, 1, 1, 1, 4])
        for column, label, key in zip(columns, (t("network"), t("timeline"), t("necessities"), t("voices")), ("network", "timeline", "necessities", "voices")):
            with column:
                st.button(label, key=f"nav-{key}", disabled=current == key, on_click=switch_view, args=(key,))


def render_sidebar(current: str, mode: str) -> None:
    with st.sidebar:
        st.title(t("project_name"))
        st.caption(t("project_navigation"))
        for label, key in (
            (t("network"), "network"),
            (t("timeline"), "timeline"),
            (t("necessities"), "necessities"),
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
        with st.container(key="language-rail"):
            for code, label in LANGUAGES.items():
                st.button(label, key=f"language-{code}", type="primary" if code == language else "secondary", use_container_width=True, on_click=set_language, args=(code,))
        st.caption(f'{t("registry")} · {mode.upper()}')
        st.caption(t("development_interface"))


def render_network(repo, mode: str) -> None:
    entities = repo.list_entities()
    relations = repo.list_relations()
    left, right = st.columns([0.8, 1.55], gap="large")
    with left:
        st.markdown('<div class="takeover-copy">', unsafe_allow_html=True)
        st.title(t("project_name"))
        st.markdown(f'<div class="takeover-kicker">{t("interactive_progress")}</div>', unsafe_allow_html=True)
        manifesto = "<br>".join(t(key) for key in ("manifesto_remains", "manifesto_doors", "manifesto_listen", "manifesto_build"))
        manifesto += "<br><br>" + "<br>".join(t(key) for key in ("manifesto_live", "manifesto_grows"))
        st.markdown(f'<div class="takeover-manifesto">{manifesto}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="takeover-entry"><strong>{t("enter_network")}</strong><span>{t("open_node")}<br>{t("explicit_relations")}</span></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        components.html(build_graph_html(entities, relations, t("start_here"), t("you"), t("invitation"), t("nodes"), t("connections"), t("connections_node")), height=610, scrolling=False)
    imperatives = "".join(f'<span class="imperative imperative-{index}">{html.escape(t(key))}</span>' for index, key in enumerate(("take_wall", "take_opening", "take_sound", "take_restaurant", "take_night", "take_web", "take_photography")))
    st.markdown(f'<section class="imperative-field"><strong>{t("project_name")}.</strong>{imperatives}<b>{t("pass_it_on")}</b></section>', unsafe_allow_html=True)
    st.markdown(f'<section class="listening"><small>{t("suggested_listening")}</small><span>{t("listening_work")}</span></section>', unsafe_allow_html=True)
    if str(st.query_params.get("door", "") or "") == "access":
        access_door()
    requested = str(st.query_params.get("node", "") or "")
    selected = next((item for item in entities if item.id == requested), None)
    if selected:
        node_dialog(selected)
    if os.getenv("TAKEOVER_ADMIN_MODE", "").strip() == "1":
        render_admin(repo, mode)


def render_admin(repo, mode: str) -> None:
    with st.expander(t("developer_add"), expanded=False):
        st.caption(t("admin_note"))
        with st.form("add-node-form", clear_on_submit=True):
            kind = st.selectbox(t("entity_type"), ENTITY_TYPES)
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
                st.success(f'{title} · {t("registry")} · {mode.upper()}')
                st.rerun()


def render_timeline() -> None:
    st.markdown(f'<div class="section-head">{t("timeline")} · {t("application")}</div>', unsafe_allow_html=True)
    payload = load_trajectory(TRAJECTORY)
    plan = payload["plan"]
    st.caption(str(plan.get("description") or t("timeline_fallback")))
    st.plotly_chart(build_timeline_figure(payload), use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
    st.caption(t("timeline_source"))


def render_necessities(repo) -> None:
    st.markdown(f'<div class="section-head">{t("necessities_title")}</div>', unsafe_allow_html=True)
    st.caption(t("need_stage_state"))
    necessities = repo.list_necessities()
    for item in sorted(necessities, key=lambda value: (value.stage, value.title)):
        st.markdown(
            f'<div class="necessity"><strong>{t(item.title)}</strong><span class="stage">{t(item.stage)}</span><span class="status">{t(item.status)}</span></div>',
            unsafe_allow_html=True,
        )
    if not necessities:
        st.info(t("no_necessities"))


def set_language(language: str) -> None:
    st.session_state["takeover_language"] = language


def render_voices() -> None:
    st.markdown('<main class="voices">', unsafe_allow_html=True)
    st.markdown(f'<div class="voices-head"><h1>{t("voices")}</h1><p>{t("voices_intro")}</p></div>', unsafe_allow_html=True)
    for utterance in UTTERANCES:
        variants = []
        for code in VOICE_LANGUAGES:
            variants.append(f'<span><b>{code.upper()} · {utterance.status(code)}</b>{html.escape(utterance.text(code))}</span>')
        weight_class = 5 if utterance.weight >= 80 else 4 if utterance.weight >= 60 else 3 if utterance.weight >= 40 else 2 if utterance.weight >= 24 else 1
        metadata = f'{t("source_key")} · {utterance.key} &nbsp; / &nbsp; {t("weight")} · {utterance.weight}'
        st.markdown(f'<article class="voice"><small class="voice-meta">{metadata}</small><div class="voice-phrase voice-weight-{weight_class}">{html.escape(utterance.text(language))}</div><div class="voice-versions">{"".join(variants)}</div><button disabled>{t("improve_translation")}</button><small>{t("proposals_closed")}</small></article>', unsafe_allow_html=True)
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
