"""Global visual language for the first TAKE OVER iteration."""

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Inter:wght@400;500;600&display=swap');
:root { --paper:#f5f2ed; --ink:#111; --muted:#68635e; --signal:#123dff; }
.stApp { background:radial-gradient(circle at 56% 38%,#fff 0,#f7f4ef 46%,#eeeae4 100%); color:var(--ink); }
[data-testid="stToolbar"] { display:none; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { border-right:1px solid rgba(17,17,17,.16); background:#ebe7e0; }
[data-testid="stSidebar"] h1 { color:var(--ink)!important; font-size:1.2rem!important; letter-spacing:.22em!important; }
[data-testid="stSidebar"] [data-testid="stButton"] button { border:0; border-radius:0; border-bottom:1px solid rgba(17,17,17,.15); background:transparent; justify-content:flex-start; font-family:'DM Mono',monospace; letter-spacing:.1em; text-transform:uppercase; }
[data-testid="stSidebar"] [data-testid="stButton"] button:hover { color:var(--signal); }
.block-container { max-width:1540px; padding:1.8rem 2.7rem 3rem; }
html, body, [class*="css"] { font-family:Inter,sans-serif; }
h1,h2,h3,p { color:var(--ink); }
h1 { font-family:'DM Mono',monospace!important; letter-spacing:.19em!important; font-size:clamp(2rem,4vw,4.2rem)!important; font-weight:500!important; }
h2,h3,.stCaption { font-family:'DM Mono',monospace!important; }
.takeover-brand { font-family:'DM Mono',monospace; letter-spacing:.42em; font-size:1.05rem; font-weight:500; }
.takeover-copy { padding-top:clamp(5rem,12vh,10rem); }
.takeover-copy h1 { margin-bottom:.35rem; }
.takeover-kicker { font-family:'DM Mono',monospace; letter-spacing:.24em; font-size:clamp(.78rem,1.1vw,1.05rem); }
.takeover-manifesto { margin-top:3rem; max-width:31rem; font-family:'DM Mono',monospace; line-height:1.65; font-size:.95rem; }
.takeover-entry { margin-top:3rem; padding-left:1rem; border-left:1px solid var(--ink); font-family:'DM Mono',monospace; }
.takeover-entry strong { display:block; letter-spacing:.18em; margin-bottom:.7rem; }
.takeover-entry span { font-size:.78rem; line-height:1.6; }
.imperative-field { position:relative; min-height:25rem; margin:4rem 0 1rem; border-top:1px solid rgba(17,17,17,.18); font-family:'DM Mono',monospace; overflow:hidden; }
.imperative-field strong { display:block; margin-top:2.2rem; font-size:clamp(2.6rem,7vw,7.5rem); line-height:.85; letter-spacing:-.07em; }
.imperative-field .imperative { position:absolute; font-size:clamp(.58rem,.75vw,.76rem); letter-spacing:.1em; color:var(--muted); }
.imperative-0{left:2%;top:52%}.imperative-1{left:24%;top:42%}.imperative-2{left:47%;top:61%}.imperative-3{right:3%;top:39%}.imperative-4{left:13%;bottom:12%}.imperative-5{left:56%;bottom:9%}.imperative-6{right:5%;bottom:24%}
.imperative-field b { position:absolute; right:2%; bottom:1%; font-size:clamp(1.5rem,3.4vw,3.8rem); letter-spacing:.02em; }
.listening { display:flex; justify-content:space-between; align-items:baseline; gap:2rem; margin:0 0 5rem; padding:1rem 0; border-top:1px solid rgba(17,17,17,.18); border-bottom:1px solid rgba(17,17,17,.18); font-family:'DM Mono',monospace; }
.listening small { color:var(--muted); letter-spacing:.15em; }.listening span { letter-spacing:.06em; }
.st-key-top-nav [data-testid="stButton"] button { border:0; background:transparent; padding:.2rem .4rem; font-family:'DM Mono',monospace; letter-spacing:.15em; font-size:.72rem; }
.st-key-top-nav [data-testid="stButton"] button:hover { color:var(--signal); border:0; }
.start-door [data-testid="stButton"] button { width:100%; min-height:5.2rem; border-radius:50%; background:#111; color:white; border:0; font-family:'DM Mono',monospace; letter-spacing:.08em; font-size:.76rem; }
.start-door [data-testid="stButton"] button:hover { background:var(--signal); color:white; border:0; }
[data-testid="stDialog"] { background:var(--paper); }
[data-testid="stDialog"] button { font-family:'DM Mono',monospace; }
.door-option { border-top:1px solid rgba(17,17,17,.18); padding:.9rem 0 .3rem; font-family:'DM Mono',monospace; }
.door-dormant { opacity:.36; }
.section-head { margin:4rem 0 2rem; font-family:'DM Mono',monospace; letter-spacing:.16em; }
.necessity { display:grid; grid-template-columns:minmax(11rem,1fr) minmax(9rem,.55fr) minmax(9rem,.55fr); gap:1.2rem; padding:1.1rem 0; border-top:1px solid rgba(17,17,17,.22); font-family:'DM Mono',monospace; font-size:.78rem; }
.necessity .status { text-transform:uppercase; letter-spacing:.08em; }
.necessity .stage { color:var(--muted); text-transform:uppercase; }
.node-kind { font-family:'DM Mono',monospace; color:var(--signal); text-transform:uppercase; letter-spacing:.13em; font-size:.73rem; }
.i18n-lab { max-width:980px; margin:clamp(4rem,9vh,8rem) auto 0; }
.i18n-eyebrow,.i18n-locale,.i18n-foot { font-family:'DM Mono',monospace; letter-spacing:.16em; font-size:.68rem; color:var(--muted); }
.i18n-eyebrow { text-align:center; margin-bottom:1.2rem; }
.st-key-language-rail { max-width:650px; margin:0 auto 4.5rem; padding:.35rem; border:1px solid rgba(17,17,17,.14); border-radius:999px; background:rgba(255,255,255,.46); }
.st-key-language-rail [data-testid="stHorizontalBlock"] { gap:.2rem; }
.st-key-language-rail [data-testid="stHorizontalBlock"] + [data-testid="stHorizontalBlock"] { margin-top:.2rem; }
.st-key-language-rail [data-testid="stButton"] button { min-height:2.6rem; border:0; border-radius:999px; font-family:'DM Mono',monospace; font-size:.75rem; background:transparent; }
.st-key-language-rail [data-testid="stButton"] button[kind="primary"] { background:#111; color:#fff; }
.i18n-locale { color:var(--signal); text-align:center; }
h1.i18n-title { margin:1.2rem auto 1.5rem!important; max-width:900px; text-align:center; font-family:Georgia,'Times New Roman',serif!important; letter-spacing:-.045em!important; font-size:clamp(3.6rem,7.5vw,7rem)!important; line-height:.88!important; font-weight:400!important; }
.i18n-title em { color:var(--signal); font-weight:400; }
.i18n-intro { max-width:590px; margin:0 auto; text-align:center; font-size:1rem; line-height:1.65; }
.i18n-rule { display:flex; align-items:center; gap:1rem; margin:4.5rem 0 2rem; color:var(--signal); font-family:'DM Mono',monospace; }
.i18n-rule span { height:1px; flex:1; background:rgba(17,17,17,.18); }
.i18n-card { min-height:210px; padding:1.6rem 0; border-top:1px solid #111; }
.i18n-card small { font-family:'DM Mono',monospace; letter-spacing:.15em; color:var(--muted); }
.i18n-card h2 { margin:.9rem 0!important; font-family:Georgia,'Times New Roman',serif!important; font-size:2rem!important; font-weight:400!important; }
.i18n-card p { max-width:35rem; line-height:1.6; color:var(--muted); }
.i18n-count strong { display:block; margin:1rem 0; font-family:Georgia,'Times New Roman',serif; font-size:2rem; font-weight:400; }
.i18n-foot { display:flex; justify-content:space-between; margin-top:3rem; padding:1rem 0; border-top:1px solid rgba(17,17,17,.18); }
.voices { max-width:1120px; margin:clamp(4rem,8vh,7rem) auto 0; }
.voices-head { display:flex; align-items:end; justify-content:space-between; gap:3rem; margin-bottom:5rem; }
.voices-head h1 { margin:0!important; }
.voices-head p { max-width:28rem; color:var(--muted); font-family:'DM Mono',monospace; font-size:.75rem; line-height:1.6; }
.voice { position:relative; padding:2rem 0 2.4rem; border-top:1px solid rgba(17,17,17,.18); }
.voice-meta { display:block; margin-bottom:.9rem; color:var(--muted); font-family:'DM Mono',monospace; letter-spacing:.09em; text-transform:uppercase; }
.voice-phrase { max-width:900px; font-family:'DM Mono',monospace; line-height:1.04; letter-spacing:.02em; }
.voice-weight-1 { font-size:.9rem; }
.voice-weight-2 { font-size:1.15rem; }
.voice-weight-3 { font-size:1.65rem; }
.voice-weight-4 { font-size:2.5rem; }
.voice-weight-5 { font-size:4.2rem; }
.voice-versions { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; max-height:0; overflow:hidden; opacity:0; transition:max-height .25s ease,opacity .25s ease; }
.voice:hover .voice-versions,.voice:focus-within .voice-versions { max-height:12rem; margin-top:1.6rem; opacity:1; }
.voice-versions span { color:var(--muted); font-size:.72rem; line-height:1.45; }
.voice-versions b { display:block; margin-bottom:.35rem; color:var(--ink); font-family:'DM Mono',monospace; letter-spacing:.14em; }
.voice button { margin-top:1rem; padding:0; border:0; background:transparent; color:#77736e; font-family:'DM Mono',monospace; font-size:.62rem; letter-spacing:.12em; }
.voice small { margin-left:1rem; color:#aaa6a0; font-family:'DM Mono',monospace; font-size:.6rem; }
@media(max-width:850px){ .block-container{padding:1.2rem}.takeover-copy{padding-top:3rem}.necessity{grid-template-columns:1fr 1fr}.imperative-field{min-height:31rem}.listening{display:block}.listening span{display:block;margin-top:.5rem} }
@media(max-width:850px){ .voices-head{display:block}.voice-versions{grid-template-columns:1fr 1fr}.voice:hover .voice-versions{max-height:24rem} }
</style>
"""
