"""Isolated visual test for the application-file CTA geometry."""

from __future__ import annotations

import html

import streamlit as st


APPLICATION_FILE_URL = "https://console.filebase.com/object/takeover-fotografiska/APPLICATION-TAKEOVER%E2%80%A2HANDOUT.pdf"


st.set_page_config(page_title="TAKE OVER · CTA turn test", page_icon="↗", layout="wide")
st.title("CTA / TURN TEST")
st.caption("ISOLATED STUDY · NO CHANGE TO THE LIVE LANDING PAGE")

turn = st.slider("TURN / DEGREES", min_value=-8.0, max_value=8.0, value=-3.0, step=0.5)
cut = st.slider("CORNER CUT / PERCENT", min_value=4, max_value=24, value=14, step=1)

state_rows = (
    ("PARTICIPANTS", "UNKNOWN"),
    ("PRODUCTION BUDGET", "NONE SECURED"),
    ("JURY", "UNKNOWN"),
    ("SELECTION", "UNKNOWN"),
    ("RESPONSE TIME", "UNKNOWN"),
    ("EXHIBITION / FEASIBILITY", "CONDITIONAL"),
    ("FUTURE CONTRIBUTORS", "OPEN"),
    ("NEXT STATE", "UNRESOLVED"),
)
rows = "".join(
    f"<div><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>"
    for label, value in state_rows
)

st.markdown(
    f"""
    <style>
      .cta-turn-sheet {{
        --turn:{turn}deg;
        --cut:{cut}%;
        position:relative;
        max-width:760px;
        min-height:880px;
        margin:2rem auto 5rem;
        padding:4.5rem 5rem;
        overflow:hidden;
        border:1px solid rgba(17,17,17,.28);
        background:#f5f2ed;
        color:#111;
        font-family:'DM Mono','Courier New',monospace;
        box-shadow:0 22px 70px rgba(17,17,17,.08);
      }}
      .cta-turn-sheet::before,.cta-turn-sheet::after {{
        content:"";position:absolute;inset:1.5rem;border-left:1px solid rgba(17,17,17,.16);border-right:1px solid rgba(17,17,17,.16);pointer-events:none;
      }}
      .cta-turn-sheet::after {{ inset:auto 2rem 5.6rem; height:1px; border:0; background:rgba(17,17,17,.22); transform:rotate(-1.2deg); }}
      .cta-turn-heading {{ margin:0 0 4rem; font-size:clamp(3.2rem,8vw,6.5rem); font-weight:500; letter-spacing:.2em; line-height:.88; }}
      .cta-turn-kicker {{ padding-bottom:1rem;border-bottom:2px solid #111;font-size:1rem;letter-spacing:.2em; }}
      .cta-turn-window {{ display:flex;justify-content:space-between;gap:2rem;padding:1.3rem 0;border-bottom:1px solid rgba(17,17,17,.24);font-size:.85rem;line-height:1.55;letter-spacing:.08em; }}
      .cta-turn-state {{ margin-top:1.5rem; }}
      .cta-turn-state>small {{ display:block;padding-bottom:.8rem;border-bottom:1px solid rgba(17,17,17,.25);font-size:.7rem;letter-spacing:.15em; }}
      .cta-turn-state>div {{ display:flex;justify-content:space-between;gap:2rem;padding:.63rem 0;border-bottom:1px solid rgba(17,17,17,.17);font-size:.72rem;letter-spacing:.04em; }}
      .cta-turn-state strong {{ font-weight:500;text-align:right; }}
      .cta-turn-action-wrap {{ position:relative;margin:8rem -2rem 0;transform:rotate(var(--turn));transform-origin:50% 50%;filter:drop-shadow(4px 6px 0 rgba(17,17,17,.16)); }}
      .cta-turn-action {{
        display:grid;grid-template-columns:1fr auto;align-items:center;gap:2rem;
        min-height:210px;padding:3rem calc(var(--cut) + 1rem);
        clip-path:polygon(var(--cut) 8%,100% 0,calc(100% - var(--cut)) 92%,0 100%);
        background:#ff4b16;color:#111!important;text-decoration:none!important;
        transition:transform .18s ease,background .18s ease;
      }}
      .cta-turn-action:hover,.cta-turn-action:focus-visible {{ transform:translateY(-5px);background:#ff641f;color:#111!important; }}
      .cta-turn-action small,.cta-turn-action strong {{ display:block;color:inherit!important; }}
      .cta-turn-action small {{ margin-bottom:.85rem;font-size:.72rem;letter-spacing:.13em; }}
      .cta-turn-action strong {{ font-size:clamp(1.05rem,2.2vw,1.55rem);letter-spacing:.08em;line-height:1.15; }}
      .cta-turn-arrow {{ font-size:3rem;line-height:1;transform:rotate(calc(-1 * var(--turn))); }}
      .cta-turn-construction {{ position:absolute;left:5%;right:5%;bottom:4.6rem;border-top:1px dashed rgba(17,17,17,.27); }}
      .cta-turn-construction::before,.cta-turn-construction::after {{ content:"";position:absolute;top:-4px;width:7px;height:7px;border-radius:50%;background:#111; }}
      .cta-turn-construction::before {{ left:0 }} .cta-turn-construction::after {{ right:0 }}
      @media(max-width:760px) {{ .cta-turn-sheet{{padding:3rem 1.4rem;min-height:800px}}.cta-turn-action-wrap{{margin:6rem 0 0}}.cta-turn-action{{padding:2rem calc(var(--cut) + .5rem);min-height:180px}} }}
    </style>
    <section class="cta-turn-sheet">
      <h1 class="cta-turn-heading">TAKE OVER</h1>
      <div class="cta-turn-kicker">INTERACTIVE IN PROGRESS</div>
      <div class="cta-turn-window"><strong>APPLICATION WINDOW /<br>OPEN</strong><span>D0 · BEFORE<br>SUBMISSION</span></div>
      <section class="cta-turn-state"><small>CURRENT STATE</small>{rows}</section>
      <div class="cta-turn-action-wrap">
        <a class="cta-turn-action" href="{APPLICATION_FILE_URL}" target="_blank" rel="noopener noreferrer">
          <span><small>APPLICATION / PDF</small><strong>OPEN APPLICATION FILE</strong></span>
          <b class="cta-turn-arrow" aria-hidden="true">↗</b>
        </a>
      </div>
      <div class="cta-turn-construction" aria-hidden="true"></div>
    </section>
    """,
    unsafe_allow_html=True,
)
