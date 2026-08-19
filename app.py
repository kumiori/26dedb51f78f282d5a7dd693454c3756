"""TAKE OVER — Milestone 2.0 operating surface."""

from __future__ import annotations

import os
from pathlib import Path
import re
import html

import streamlit as st
import streamlit.components.v1 as components

from takeover.call import load_call
from takeover.graph import build_graph_html
from takeover.events import list_events, record_event, record_event_once
from takeover.i18n import LANGUAGES, REGISTRY, UTTERANCES, VOICE_LANGUAGES, language_status_metrics, language_term, record_translation_proposal, translate
from takeover.models import ENTITY_TYPES, STAGES, Entity
from takeover.registry import SessionRegistry
from takeover.resources import build_resources_figure, load_resources
from takeover.style import CSS
from takeover.timeline import build_time_mapping_figure, build_time_mapping_rows, build_timeline_figure, load_trajectory


ROOT = Path(__file__).resolve().parent
TRAJECTORY = ROOT / "config" / "takeover_trajectory.yaml"
RESOURCES = ROOT / "config" / "takeover_resources.yaml"
CALL = ROOT / "config" / "takeover_call.yaml"

language = st.session_state.get("takeover_language", "en")
if language not in LANGUAGES:
    language = "en"
t = lambda key: translate(key, language)

st.set_page_config(page_title=t("project_name"), page_icon="+", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)
record_event_once(st.session_state, "session-started", "event_session_started")


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
    record_event(st.session_state, "event_navigate", view)


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
        columns = st.columns([1, 1, 1, 1, 1, 3])
        for column, label, key in zip(columns, (t("process"), t("timeline"), t("needs"), t("resources"), t("voices")), ("network", "timeline", "necessities", "resources", "voices")):
            with column:
                st.button(label, key=f"nav-{key}", disabled=current == key, on_click=switch_view, args=(key,))


def render_sidebar_voice_statistics() -> None:
    metrics = language_status_metrics()
    eligible_recordings = {utterance.key for utterance in UTTERANCES if utterance.weight >= 30}
    completed_recordings = {
        event["target"] for event in list_events(st.session_state)
        if event.get("label_key") == "event_recording_ready" and event.get("target") in eligible_recordings
    }
    proposals = st.session_state.get("takeover_translation_proposals", [])
    translation_capacity = len(UTTERANCES) * (len(VOICE_LANGUAGES) - 1)
    status_totals = {status: sum(item[status] for item in metrics.values()) for status in ("CANONICAL", "PROVISIONAL", "UNTRANSLATED")}
    status_capacity = sum(status_totals.values()) or 1
    st.markdown(f'<div class="sidebar-analysis-title">{t("voices_statistics")}</div>', unsafe_allow_html=True)
    for label, value, capacity in (
        (t("recordings_complete"), len(completed_recordings), len(eligible_recordings)),
        (t("translation_proposals"), len(proposals), translation_capacity),
        (t("corpus_status"), status_totals["CANONICAL"] + status_totals["PROVISIONAL"], status_capacity),
    ):
        st.markdown(f'<div class="sidebar-stat"><small>{label}</small><strong>{value} / {capacity}</strong><span>{100 * value / max(1, capacity):.1f}%</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-analysis-subtitle">{t("language_status")}</div>', unsafe_allow_html=True)
    for code in VOICE_LANGUAGES:
        counts = metrics[code]
        total = sum(counts.values()) or 1
        segments = "".join(f'<i class="status-{status.lower()}" style="width:{100 * count / total:.2f}%"></i>' for status, count in counts.items() if count)
        detail = " · ".join(f'{status} {100 * count / total:.0f}%' for status, count in counts.items() if count)
        st.markdown(f'<div class="sidebar-language-metric"><strong>{language_term(code)}</strong><div class="status-bar">{segments}</div><small>{detail}</small></div>', unsafe_allow_html=True)


def render_sidebar_call_information() -> None:
    call = load_call(CALL)
    paragraphs = "".join(f'<p>{html.escape(str(paragraph))}</p>' for paragraph in call["paragraphs"])
    st.markdown(f'<section class="sidebar-call"><small>{html.escape(str(call["title"]).upper())}</small>{paragraphs}<strong>{html.escape(str(call["emphasis"]))}</strong></section>', unsafe_allow_html=True)


def render_sidebar_time_mapping() -> None:
    payload = load_trajectory(TRAJECTORY)
    plan = payload["plan"]
    event_rows = build_time_mapping_rows(payload)
    figure = build_time_mapping_figure(payload)
    figure.update_layout(height=360, margin={"l": 42, "r": 12, "t": 20, "b": 45}, showlegend=False, title=None)
    figure.update_xaxes(title="u · LINEAR")
    figure.update_yaxes(title="q · NONLINEAR")
    st.markdown(f'<div class="sidebar-analysis-title">{t("time_mapping")}</div>', unsafe_allow_html=True)
    st.write(t("time_mapping_note"))
    st.latex(r"u_i=\frac{d_i-d_0}{H},\quad q_i=f(u_i),\quad \Delta_i=q_i-u_i")
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
    st.markdown(f'<div class="sidebar-analysis-title">{t("datasets")}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-stat">'
        f'<small>{t("phase")}</small><strong>{t("application")}</strong>'
        f'<span>{html.escape(str(plan.get("temporal_mode") or ""))}</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.dataframe([{
        "START": plan.get("start_date"),
        "HORIZON": plan.get("horizon_days"),
        "UNIT": plan.get("time_unit"),
        "LANDING": plan.get("destination_label"),
    }], use_container_width=True, hide_index=True)
    anchor_rows = [
        {"ANCHOR": str(anchor[0]), "q": float(anchor[1])}
        for anchor in plan.get("qualitative_anchors") or []
    ]
    st.markdown(f'<div class="sidebar-analysis-subtitle">QUALITATIVE ANCHORS</div>', unsafe_allow_html=True)
    st.dataframe(anchor_rows, use_container_width=True, hide_index=True)
    st.markdown(f'<div class="sidebar-analysis-subtitle">{t("trajectory_dataset")}</div>', unsafe_allow_html=True)
    st.dataframe([
        {
            "DATE": row["date"],
            "EVENT": row["title"],
            "TYPE": row["type"],
            "u": round(row["linear"], 3),
            "q": round(row["nonlinear"], 3),
            "Δ": round(row["residual"], 3),
            "VISIBILITY": row["visibility"],
        }
        for row in event_rows
    ], use_container_width=True, hide_index=True)


def render_sidebar(current: str, mode: str) -> None:
    with st.sidebar:
        st.title(t("project_name"))
        st.caption(t("project_navigation"))
        for label, key in (
            (t("process"), "network"),
            (t("timeline"), "timeline"),
            (t("needs"), "necessities"),
            (t("resources"), "resources"),
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
        st.caption(f'{t("registry")} · {mode.upper()}')
        st.caption(t("development_interface"))
        if current == "network":
            render_sidebar_call_information()
        elif current == "timeline":
            render_sidebar_time_mapping()
        elif current == "voices":
            render_sidebar_voice_statistics()
        st.markdown(f'<div class="event-log-title">{t("event_log")}</div>', unsafe_allow_html=True)
        for event in reversed(list_events(st.session_state)):
            occurred = str(event.get("occurred_at") or "")[11:19]
            label_key = str(event.get("label_key") or "")
            label = t(label_key) if label_key in REGISTRY else label_key
            target = html.escape(str(event.get("target") or ""))
            detail = html.escape(str(event.get("detail") or ""))
            suffix = " · ".join(value for value in (target, detail) if value)
            st.markdown(f'<div class="event-log-row"><time>{occurred} UTC</time><strong>{html.escape(label)}</strong>{f"<span>{suffix}</span>" if suffix else ""}</div>', unsafe_allow_html=True)


def render_network(repo, mode: str) -> None:
    entities = repo.list_entities()
    relations = repo.list_relations()
    left, right = st.columns([0.8, 1.55], gap="large")
    with left:
        st.markdown('<div class="takeover-copy">', unsafe_allow_html=True)
        st.title(t("project_name"))
        st.markdown(f'<div class="takeover-kicker">{t("interactive_progress")}</div>', unsafe_allow_html=True)
        process = "".join(
            f'<p>{html.escape(t(key))}</p>'
            for key in ("take_wall", "take_oven", "take_sound", "take_restaurant", "take_night", "take_web")
        )
        st.markdown(f'<div class="takeover-process">{process}</div>', unsafe_allow_html=True)
        manifesto = "<br>".join(t(key) for key in ("manifesto_remains", "manifesto_doors", "manifesto_listen", "manifesto_build"))
        manifesto += "<br><br>" + "<br>".join(t(key) for key in ("manifesto_live", "manifesto_grows"))
        st.markdown(f'<div class="takeover-manifesto">{manifesto}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="takeover-entry"><strong>{t("landing_action")}</strong><span>{t("open_node")}</span></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        components.html(build_graph_html(entities, relations, t("start_here"), t("you"), t("invitation"), t("nodes"), t("connections"), t("connections_node")), height=610, scrolling=False)
    st.markdown(f'<section class="handoff">{t("pass_it_on")}</section>', unsafe_allow_html=True)
    st.markdown(f'<section class="listening"><small>{t("suggested_listening")}</small><span>{t("listening_work")}</span></section>', unsafe_allow_html=True)
    if str(st.query_params.get("door", "") or "") == "access":
        record_event_once(st.session_state, "access-door-open", "event_access_opened")
        access_door()
    requested = str(st.query_params.get("node", "") or "")
    selected = next((item for item in entities if item.id == requested), None)
    if selected:
        record_event_once(st.session_state, f"node-open-{selected.id}", "event_node_opened", selected.id)
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
                record_event(st.session_state, "event_entity_added", clean_id)
                st.success(f'{title} · {t("registry")} · {mode.upper()}')
                st.rerun()


def render_timeline() -> None:
    st.markdown(f'<div class="section-head">{t("timeline")} · {t("application")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="timeline-phase">{t("phase")}: {t("application")}</div>', unsafe_allow_html=True)
    payload = load_trajectory(TRAJECTORY)
    st.caption(t("timeline_proposition"))
    st.plotly_chart(build_timeline_figure(payload), use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
    st.caption(t("timeline_source"))


def render_necessities(repo) -> None:
    st.markdown(f'<div class="section-head">{t("necessities_title")}</div>', unsafe_allow_html=True)
    st.caption(t("need_stage_state"))
    necessities = repo.list_necessities()
    st.markdown(f'<div class="necessity necessity-head"><strong>{t("need")}</strong><span>{t("stage")}</span><span>{t("state")}</span></div>', unsafe_allow_html=True)
    for item in necessities:
        name = t(item.title) if item.title in REGISTRY else item.title
        stage = t(item.stage) if item.stage in REGISTRY else item.stage.upper()
        status = t(item.status) if item.status in REGISTRY else item.status.upper()
        if item.title == "application" and item.status == "to_submit":
            status = f'{t("to_submit")} → {t("done")}'
        st.markdown(
            f'<div class="necessity{" dormant" if item.status == "not_yet_activated" else ""}"><strong>{html.escape(name)}</strong><span class="stage">{html.escape(stage)}</span><span class="status">{html.escape(status)}</span></div>',
            unsafe_allow_html=True,
        )
    if not necessities:
        st.info(t("no_necessities"))


def render_resources() -> None:
    trajectory = load_trajectory(TRAJECTORY)
    resource_plan = load_resources(RESOURCES)
    st.markdown(f'<div class="section-head">{t("resources")} · {t("application")}</div>', unsafe_allow_html=True)
    st.write(t("resources_intro"))
    st.caption(t("observed_intention"))
    st.plotly_chart(build_resources_figure(trajectory, resource_plan), use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
    st.markdown(f'<div class="analysis-head">{t("datasets")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dataset-label">{t("allocated_dataset")}</div>', unsafe_allow_html=True)
    st.dataframe(resource_plan["allocated_resources"]["observations"], use_container_width=True, hide_index=True)
    st.markdown(f'<div class="dataset-label">{t("intentions_dataset")}</div>', unsafe_allow_html=True)
    st.dataframe(resource_plan["investment_intentions"], use_container_width=True, hide_index=True)
    trajectory_rows = [
        {"id": item.get("id"), "date": item.get("date"), "type": item.get("type"), "title": item.get("title"), "q": item.get("time_parameter")}
        for item in sorted(trajectory["primitives"], key=lambda value: float(value.get("time_parameter", 0)))
    ]
    st.markdown(f'<div class="dataset-label">{t("trajectory_dataset")}</div>', unsafe_allow_html=True)
    st.dataframe(trajectory_rows, use_container_width=True, hide_index=True)


def set_language(language: str) -> None:
    previous = st.session_state.get("takeover_language", "en")
    st.session_state["takeover_language"] = language
    record_event(st.session_state, "event_language_changed", f"{previous} → {language}")


def log_reading_languages() -> None:
    selected = st.session_state.get("voices-reading-languages", [])
    record_event(st.session_state, "event_reading_languages", ", ".join(str(code) for code in selected))


@st.dialog(t("voice_recording"), width="large")
def voice_recording_dialog(utterance) -> None:
    st.markdown(f'<div class="recording-utterance">{html.escape(utterance.text(language))}</div>', unsafe_allow_html=True)
    st.write(t("recording_prompt"))
    recording = st.audio_input(t("start_recording"), key=f"visitor-voice-recording-{utterance.key}")
    if recording is not None:
        record_event_once(st.session_state, f"recording-ready-{utterance.key}", "event_recording_ready", utterance.key)
        st.audio(recording)
        st.caption(t("recording_ready"))


@st.dialog(t("add_translation"), width="large")
def translation_proposal_dialog(utterance) -> None:
    target_languages = tuple(code for code in VOICE_LANGUAGES if code != "en")
    target = st.selectbox(t("translation_language"), target_languages, format_func=language_term, key=f"translation-language-{utterance.key}")
    st.caption(t("original"))
    st.markdown(f'<div class="translation-source">{html.escape(utterance.canonical)}</div>', unsafe_allow_html=True)
    st.caption(t("current_translation"))
    st.markdown(f'<div class="translation-current">{html.escape(utterance.text(target))}</div>', unsafe_allow_html=True)
    with st.form(f"translation-proposal-{utterance.key}", clear_on_submit=True):
        proposal = st.text_area(t("your_version"), key=f"translation-version-{utterance.key}")
        submitted = st.form_submit_button(t("propose_translation"), use_container_width=True)
    if submitted:
        if not proposal.strip():
            st.error(t("translation_required"))
        else:
            record_translation_proposal(st.session_state, utterance.key, target, proposal)
            record_event(st.session_state, "event_translation_saved", utterance.key, target)
            st.success(t("translation_saved"))


def render_voices() -> None:
    st.markdown('<main class="voices">', unsafe_allow_html=True)
    st.markdown(f'<div class="voices-head"><h1>{t("voices")}</h1><p>{t("voices_intro")}</p></div>', unsafe_allow_html=True)
    with st.container(key="voices-language-rail"):
        language_items = list(LANGUAGES.items())
        for row_start in range(0, len(language_items), 4):
            columns = st.columns(4)
            for column, (code, label) in zip(columns, language_items[row_start:row_start + 4]):
                with column:
                    st.button(
                        language_term(code),
                        key=f"voice-language-{code}",
                        type="primary" if code == language else "secondary",
                        use_container_width=True,
                        on_click=set_language,
                        args=(code,),
                    )
    st.markdown(f'<div class="voice-contribution-key"><span>🎙</span><strong>{t("record_voice")}</strong><span>+</span><strong>{t("add_translation")}</strong><small>{t("voice_contribution_intro")}</small></div>', unsafe_allow_html=True)
    reading_languages = st.multiselect(
        t("languages_to_read"),
        options=VOICE_LANGUAGES,
        default=VOICE_LANGUAGES,
        format_func=language_term,
        key="voices-reading-languages",
        on_change=log_reading_languages,
    )
    for utterance in UTTERANCES:
        variants = []
        for code in reading_languages:
            variants.append(f'<span><b>{code.upper()} · {utterance.status(code)}</b>{html.escape(utterance.text(code))}</span>')
        weight_class = 5 if utterance.weight >= 80 else 4 if utterance.weight >= 60 else 3 if utterance.weight >= 40 else 2 if utterance.weight >= 24 else 1
        metadata = f'{t("source_key")} · {utterance.key} &nbsp; / &nbsp; {t("weight")} · {utterance.weight}'
        article = f'<article class="voice"><small class="voice-meta">{metadata}</small><div class="voice-phrase voice-weight-{weight_class}">{html.escape(utterance.text(language))}</div><div class="voice-versions">{"".join(variants)}</div><button disabled>{t("improve_translation")}</button><small>{t("proposals_closed")}</small></article>'
        text_column, record_column, translation_column = st.columns([12, 1, 1], vertical_alignment="top")
        with text_column:
            st.markdown(article, unsafe_allow_html=True)
        with record_column:
            if utterance.weight >= 30:
                if st.button("🎙", key=f"record-voice-{utterance.key}", help=t("record_voice")):
                    record_event(st.session_state, "event_recording_opened", utterance.key)
                    voice_recording_dialog(utterance)
        with translation_column:
            if st.button("+", key=f"add-translation-{utterance.key}", help=t("add_translation")):
                record_event(st.session_state, "event_translation_opened", utterance.key)
                translation_proposal_dialog(utterance)
    st.markdown('</main>', unsafe_allow_html=True)


repo, registry_mode = registry()
current_view = st.session_state.get("takeover_view") or str(st.query_params.get("view", "network"))
if current_view not in {"network", "timeline", "necessities", "resources", "voices"}:
    current_view = "network"
render_nav(current_view)
render_sidebar(current_view, registry_mode)
if current_view == "network":
    render_network(repo, registry_mode)
elif current_view == "timeline":
    render_timeline()
elif current_view == "necessities":
    render_necessities(repo)
elif current_view == "resources":
    render_resources()
else:
    render_voices()
