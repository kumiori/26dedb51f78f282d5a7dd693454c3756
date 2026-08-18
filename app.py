"""TAKE OVER — Milestone 1 Streamlit scaffold."""

from __future__ import annotations

import os
from pathlib import Path
import re

import streamlit as st
import streamlit.components.v1 as components

from takeover.graph import build_graph_html
from takeover.i18n import LANGUAGES, translator
from takeover.models import ENTITY_TYPES, STAGES, Entity
from takeover.registry import SessionRegistry
from takeover.style import CSS
from takeover.timeline import build_timeline_figure, load_trajectory


ROOT = Path(__file__).resolve().parent
TRAJECTORY = ROOT / "config" / "takeover_trajectory.yaml"

st.set_page_config(page_title="TAKE OVER", page_icon="+", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


def _notion_token_value() -> str:
    token = os.getenv("NOTION_TOKEN", "").strip() or _secret("NOTION_TOKEN")
    if token:
        return token
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


@st.dialog("ACCESS DOOR", width="large")
def access_door() -> None:
    st.caption("A PROJECT IN FORMATION")
    st.markdown("The door opens onto what exists now. Other routes remain visible, but unopened.")
    st.markdown('<div class="door-option">FOLLOW THE TRAJECTORY</div>', unsafe_allow_html=True)
    st.button("Open timeline →", width="stretch", on_click=switch_view, args=("timeline",))
    st.markdown('<div class="door-option">SEE WHAT IS NEEDED</div>', unsafe_allow_html=True)
    st.button("Open necessities →", width="stretch", on_click=switch_view, args=("necessities",))
    st.markdown('<div class="door-option door-dormant">CONTRIBUTE — UNOPENED</div>', unsafe_allow_html=True)
    st.button("This door is not active yet", disabled=True, width="stretch")
    st.markdown('<div class="door-option door-dormant">EXPLORE — DORMANT</div>', unsafe_allow_html=True)


@st.dialog("NODE", width="large")
def node_dialog(entity: Entity) -> None:
    st.markdown(f'<div class="node-kind">{entity.type}</div>', unsafe_allow_html=True)
    st.header(entity.title)
    if entity.label:
        st.write(entity.label)
    st.caption(f"STAGE · {entity.stage.upper()}   /   STATUS · {entity.status.upper()}")
    if entity.source:
        st.write(entity.source)
    if entity.metadata:
        for key, value in entity.metadata.items():
            st.write(f"{key}: {value}")
    st.caption(f"REGISTRY ID · {entity.id}")


def render_nav(current: str) -> None:
    st.markdown('<div class="takeover-brand">TAKE OVER</div>', unsafe_allow_html=True)
    with st.container(key="top-nav"):
        columns = st.columns([1, 1, 1, 1, 4])
        for column, label, key in zip(columns, ("NETWORK", "TIMELINE", "NECESSITIES", "I18N LAB"), ("network", "timeline", "necessities", "i18n")):
            with column:
                st.button(label, key=f"nav-{key}", disabled=current == key, on_click=switch_view, args=(key,))


def render_sidebar(current: str, mode: str) -> None:
    with st.sidebar:
        st.title("TAKE OVER")
        st.caption("PROJECT NAVIGATION")
        for label, key in (
            ("Network", "network"),
            ("Timeline", "timeline"),
            ("Necessities", "necessities"),
            ("I18n lab", "i18n"),
        ):
            st.button(
                label,
                key=f"sidebar-{key}",
                disabled=current == key,
                width="stretch",
                on_click=switch_view,
                args=(key,),
            )
        st.divider()
        st.caption(f"REGISTRY · {mode.upper()}")
        st.caption("DEVELOPMENT INTERFACE")


def render_network(repo, mode: str) -> None:
    entities = repo.list_entities()
    relations = repo.list_relations()
    left, right = st.columns([0.8, 1.55], gap="large")
    with left:
        st.markdown('<div class="takeover-copy">', unsafe_allow_html=True)
        st.title("TAKE OVER")
        st.markdown('<div class="takeover-kicker">A COMMUNITY IN PROGRESS</div>', unsafe_allow_html=True)
        st.markdown('<div class="takeover-manifesto">We start from what remains.<br>We open doors.<br>We listen. We respond.<br>We build what comes next — together.<br><br>This is a live project.<br>It grows with every connection.</div>', unsafe_allow_html=True)
        st.markdown('<div class="takeover-entry"><strong>ENTER THE NETWORK</strong><span>Open the central node to begin.<br>The system grows from explicit relations.</span></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        if entities:
            components.html(build_graph_html(entities, relations), height=610, scrolling=False)
            st.markdown('<div class="start-door">', unsafe_allow_html=True)
            if st.button("+  START HERE", key="start-populated"):
                access_door()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.write("")
            st.write("")
            middle = st.columns([2.1, .75, 2.1])[1]
            with middle:
                st.markdown('<div class="start-door">', unsafe_allow_html=True)
                if st.button("+\nSTART HERE", key="start-empty"):
                    access_door()
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:13rem'></div>", unsafe_allow_html=True)
            st.caption("THE NETWORK HAS NOT YET BEEN ACTIVATED")
    requested = str(st.query_params.get("node", "") or "")
    selected = next((item for item in entities if item.id == requested), None)
    if selected:
        node_dialog(selected)
    if os.getenv("TAKEOVER_ADMIN_MODE", "").strip() == "1":
        render_admin(repo, mode)


def render_admin(repo, mode: str) -> None:
    with st.expander("Developer controls · Add node", expanded=False):
        st.caption("Local/admin validation only. This surface is absent unless TAKEOVER_ADMIN_MODE=1.")
        with st.form("add-node-form", clear_on_submit=True):
            kind = st.selectbox("Entity type", ENTITY_TYPES)
            title = st.text_input("Name / title")
            entity_id = st.text_input("ID", placeholder="ave")
            label = st.text_input("Label", placeholder="artist")
            stage = st.selectbox("Stage", STAGES)
            source = st.text_input("Image or audio URL", placeholder="https://…")
            submitted = st.form_submit_button("Add entity", width="stretch")
        if submitted:
            clean_id = re.sub(r"[^a-z0-9_-]+", "-", entity_id.strip().lower()).strip("-")
            try:
                repo.add_entity(Entity(clean_id, kind, title.strip(), label.strip(), stage, "active", source.strip()))
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success(f"Added {title} to the {mode} registry.")
                st.rerun()


def render_timeline() -> None:
    st.markdown('<div class="section-head">TIMELINE · APPLICATION</div>', unsafe_allow_html=True)
    payload = load_trajectory(TRAJECTORY)
    plan = payload["plan"]
    st.caption(str(plan.get("description") or "A trajectory toward the opening of TAKE OVER."))
    st.plotly_chart(build_timeline_figure(payload), width="stretch", config={"displayModeBar": False, "scrollZoom": False})
    st.caption("READ-ONLY M1 VIEW · YAML REMAINS THE TIMELINE SOURCE")


def render_necessities(repo) -> None:
    st.markdown('<div class="section-head">WHAT THE PROJECT NEEDS NOW</div>', unsafe_allow_html=True)
    st.caption("Need → stage → status. This is not a resources directory.")
    necessities = repo.list_necessities()
    for item in sorted(necessities, key=lambda value: (value.stage, value.title)):
        st.markdown(
            f'<div class="necessity"><strong>{item.title}</strong><span class="stage">{item.stage}</span><span class="status">{item.status}</span><span class="desc">{item.description}</span></div>',
            unsafe_allow_html=True,
        )
    if not necessities:
        st.info("No necessities have been activated yet.")


def set_language(language: str) -> None:
    st.session_state["takeover_language"] = language


def render_i18n_lab() -> None:
    language = st.session_state.get("takeover_language", "en")
    if language not in LANGUAGES:
        language = "en"
    translation = translator(language)
    _ = translation.gettext
    ngettext = translation.ngettext

    st.markdown('<main class="i18n-lab">', unsafe_allow_html=True)
    st.markdown('<div class="i18n-eyebrow">GETTEXT · TRANSLATION SPECIMEN 01</div>', unsafe_allow_html=True)
    with st.container(key="language-rail"):
        language_items = list(LANGUAGES.items())
        for row_start in range(0, len(language_items), 4):
            row = language_items[row_start:row_start + 4]
            language_columns = st.columns(4)
            for column, (code, label) in zip(language_columns, row):
                with column:
                    st.button(
                        label,
                        key=f"language-{code}",
                        type="primary" if code == language else "secondary",
                        width="stretch",
                        on_click=set_language,
                        args=(code,),
                    )

    st.markdown(f'<div class="i18n-locale">{_("CURRENT LANGUAGE")} · {language.upper()}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="i18n-title">{_("Many voices.")}<br><em>{_("One shared space.")}</em></h1>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="i18n-intro">{_("A small laboratory for testing how TAKE OVER speaks across languages before translated copy enters the wider project.")}</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="i18n-rule"><span></span><b>+</b><span></span></div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown(f'<div class="i18n-card"><small>01 · {_("CONTEXT")}</small><h2>{_("Translation keeps its place")}</h2><p>{_("Messages are translated in context, while the project structure and source data remain unchanged.")}</p></div>', unsafe_allow_html=True)
    with right:
        count = st.slider(_("Plural-form test"), 0, 5, 2)
        plural_message = ngettext("%(count)d open door", "%(count)d open doors", count) % {"count": count}
        st.markdown(f'<div class="i18n-card i18n-count"><small>02 · NGETTEXT</small><strong>{plural_message}</strong><p>{_("This sentence changes through the catalogue’s plural rules, not a UI-only conditional.")}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="i18n-foot">{_("SOURCE COPY: ENGLISH")}<span>{_("CATALOGUE: GNU GETTEXT")}</span></div>', unsafe_allow_html=True)
    st.markdown('</main>', unsafe_allow_html=True)


repo, registry_mode = registry()
current_view = st.session_state.get("takeover_view") or str(st.query_params.get("view", "network"))
if current_view not in {"network", "timeline", "necessities", "i18n"}:
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
    render_i18n_lab()
