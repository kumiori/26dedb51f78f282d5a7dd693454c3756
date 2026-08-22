"""Global visual language for TAKE OVER M2.0."""

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Inter:wght@400;500;600&display=swap');
:root { --paper:#f5f2ed; --ink:#111; --muted:#68635e; --signal:#315f78; }
.stApp { background:radial-gradient(circle at 56% 38%,#fff 0,#f7f4ef 46%,#eeeae4 100%); color:var(--ink); }
[data-testid="stToolbar"] { display:none; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { border-right:1px solid rgba(17,17,17,.16); background:#ebe7e0; }
[data-testid="stSidebar"] h1 { color:var(--ink)!important; font-size:1.2rem!important; letter-spacing:.22em!important; }
[data-testid="stSidebar"] [data-testid="stButton"] button { border:0; border-radius:0; border-bottom:1px solid rgba(17,17,17,.15); background:transparent; justify-content:flex-start; font-family:'DM Mono',monospace; letter-spacing:.1em; text-transform:uppercase; }
[data-testid="stSidebar"] [data-testid="stButton"] button:hover { color:var(--signal); }
.event-log-title { margin:2rem 0 .5rem; padding-top:.8rem; border-top:1px solid rgba(17,17,17,.35); color:#111; font-family:'DM Mono',monospace; font-size:.7rem; font-weight:500; letter-spacing:.14em; }
.event-log-row { padding:.6rem 0; border-top:1px solid rgba(17,17,17,.22); color:#111; font-family:'DM Mono',monospace; line-height:1.35; }
.event-log-row time,.event-log-row strong,.event-log-row span { display:block; }
.event-log-row time { color:#48443f; font-size:.57rem; font-weight:500; letter-spacing:.06em; }
.event-log-row strong { margin-top:.18rem; color:#111; font-size:.63rem; font-weight:500; letter-spacing:.05em; }
.event-log-row span { margin-top:.14rem; color:#3f3b37; font-size:.59rem; overflow-wrap:anywhere; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a { border:1px solid #111; border-radius:0; font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.1em; }
.sidebar-analysis-title,.sidebar-call>small { display:block; margin:2rem 0 .8rem; padding-top:.8rem; border-top:1px solid rgba(17,17,17,.35); color:#111; font-family:'DM Mono',monospace; font-size:.68rem; font-weight:500; letter-spacing:.13em; }
.sidebar-analysis-subtitle { margin:1.2rem 0 .45rem; color:#111; font-family:'DM Mono',monospace; font-size:.61rem; letter-spacing:.1em; }
.sidebar-stat { padding:.65rem 0; border-top:1px solid rgba(17,17,17,.2); font-family:'DM Mono',monospace; }
.sidebar-stat small,.sidebar-stat strong,.sidebar-stat span { display:block; color:#111; }.sidebar-stat small{font-size:.58rem;letter-spacing:.06em}.sidebar-stat strong{margin-top:.2rem;font-size:1rem;font-weight:500}.sidebar-stat span{font-size:.62rem}
.sidebar-language-metric { padding:.5rem 0; border-top:1px solid rgba(17,17,17,.16); font-family:'DM Mono',monospace; }.sidebar-language-metric strong{display:block;margin-bottom:.35rem;color:#111;font-size:.57rem}.sidebar-language-metric small{display:block;margin-top:.3rem;color:#3f3b37;font-size:.52rem;line-height:1.35}
.sidebar-call p { margin:0 0 1rem; color:#24211f; font-size:.72rem; line-height:1.55; }
.sidebar-call>strong { display:block; margin:1.5rem 0; padding:.8rem 0; border-top:2px solid #111; border-bottom:2px solid #111; color:#111; font-family:'DM Mono',monospace; font-size:1rem; line-height:1.12; text-transform:uppercase; }
.block-container { max-width:1540px; padding:1.8rem 2.7rem 3rem; }
html, body, [class*="css"] { font-family:Inter,sans-serif; }
h1,h2,h3,p { color:var(--ink); }
h1 { font-family:'DM Mono',monospace!important; letter-spacing:.19em!important; font-size:clamp(2.625rem,3.2vw,3rem)!important; font-weight:500!important; }
h2,h3,.stCaption { font-family:'DM Mono',monospace!important; }
.takeover-brand { font-family:'DM Mono',monospace; letter-spacing:.42em; font-size:1.05rem; font-weight:500; }
.takeover-copy { padding-top:clamp(5rem,12vh,10rem); }
.takeover-copy h1 { margin-bottom:.35rem; font-size:clamp(3.25rem,4.2vw,3.75rem)!important; line-height:.94!important; }
.takeover-kicker { font-family:'DM Mono',monospace; letter-spacing:.24em; font-size:clamp(.8125rem,.9vw,.875rem); }
.takeover-three-blocks { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:clamp(1.5rem,4vw,4rem); margin:3.5rem 0 1rem; padding:2rem 0; border-top:1px solid rgba(17,17,17,.18); }
.application-state { display:flex; justify-content:space-between; gap:1rem; margin-top:1.5rem; padding:.7rem 0; border-top:2px solid var(--ink); border-bottom:1px solid rgba(17,17,17,.25); font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.1em; }
.application-state span { color:var(--muted); }
.uncertainty-state { margin-top:1rem; font-family:'DM Mono',monospace; }
.uncertainty-state>small { display:block; margin-bottom:.45rem; color:var(--muted); font-size:.58rem; letter-spacing:.15em; }
.uncertainty-state>div { display:flex; justify-content:space-between; gap:1rem; padding:.25rem 0; border-top:1px solid rgba(17,17,17,.13); font-size:.58rem; letter-spacing:.055em; }
.uncertainty-state b { font-weight:500; text-align:right; }
.uncertainty-state p { margin:.8rem 0 0; color:var(--muted); font-size:.64rem; line-height:1.45; }
.application-file-action { display:grid; grid-template-columns:2rem 1fr auto; align-items:center; gap:.85rem; min-height:158px; margin:2.5rem -1.1rem 1.2rem; padding:2rem 12%; border:1px solid #111; clip-path:polygon(14% 8%,100% 0,86% 92%,0 100%); background:#ff4b16; color:#111!important; filter:drop-shadow(5px 7px 0 rgba(17,17,17,.18)); text-decoration:none!important; transform:rotate(-3deg); transform-origin:50% 50%; transition:transform .16s ease,filter .16s ease,background .16s ease; }
.application-file-action:hover,.application-file-action:focus-visible { transform:rotate(-3deg) translateY(-5px); background:#ff641f; filter:drop-shadow(7px 10px 0 rgba(17,17,17,.22)); color:#111!important; }
.application-file-action svg { width:1.9rem; height:1.9rem; fill:currentColor; }
.application-file-action span,.application-file-action span small,.application-file-action span strong { display:block; color:inherit!important; }
.application-file-action span small { margin-bottom:.55rem; font-size:.52rem; letter-spacing:.15em; opacity:.72; }
.application-file-action span strong { font-size:clamp(.72rem,1.15vw,.92rem); line-height:1.15; letter-spacing:.075em; }
.application-file-action>b { color:#111; font-size:1.65rem; transform:rotate(3deg); }
.takeover-process { margin-top:0; padding-left:1rem; border-left:2px solid var(--signal); font-family:'DM Mono',monospace; }
.takeover-process p { margin:0 0 .58rem; font-size:.8125rem; line-height:1.4; }
.takeover-process p:last-child { margin-bottom:0; }
.takeover-manifesto { margin-top:0; max-width:31rem; font-family:'DM Mono',monospace; line-height:1.6; font-size:.8125rem; }
.takeover-entry { margin-top:0; padding-left:1rem; border-left:1px solid var(--ink); font-family:'DM Mono',monospace; }
.takeover-entry strong { display:block; letter-spacing:.18em; margin-bottom:.7rem; }
.takeover-entry span { font-size:.8125rem; line-height:1.6; }
.handoff { margin:4rem 0 1rem; padding:2rem 0; border-top:1px solid rgba(17,17,17,.18); font-family:'DM Mono',monospace; font-size:clamp(1.5rem,3.4vw,3.8rem); font-weight:500; text-align:right; }
.listening { display:flex; justify-content:space-between; align-items:baseline; gap:2rem; margin:0 0 5rem; padding:1rem 0; border-top:1px solid rgba(17,17,17,.18); border-bottom:1px solid rgba(17,17,17,.18); font-family:'DM Mono',monospace; }
.listening small { color:var(--muted); letter-spacing:.15em; }.listening span { letter-spacing:.06em; }
.listening-addendum { max-width:44rem; margin:4rem 0 2rem; }
.listening-addendum small,.listening-item small,.listening-item footer { color:var(--muted); font-family:'DM Mono',monospace; font-size:.62rem; letter-spacing:.12em; }
.listening-addendum h2 { margin:.8rem 0 1rem!important; font-family:Georgia,'Times New Roman',serif!important; font-size:clamp(2.4rem,5vw,4.6rem)!important; font-weight:400!important; }
.listening-addendum p { max-width:36rem; line-height:1.6; }
.listening-item { display:grid; grid-template-columns:minmax(10rem,.55fr) minmax(18rem,1fr); gap:.4rem 2rem; padding:1.4rem 0; border-top:1px solid rgba(17,17,17,.18); }
.listening-item small,.listening-item strong,.listening-item span { grid-column:1; }.listening-item h3,.listening-item p,.listening-item footer { grid-column:2; }
.listening-item h3 { grid-row:1 / span 2; margin:0!important; font-family:Georgia,'Times New Roman',serif!important; font-size:1.6rem!important; font-weight:400!important; }
.listening-item strong,.listening-item span { font-family:'DM Mono',monospace; font-size:.7rem; }.listening-item p { margin:.7rem 0; line-height:1.55; }.listening-item footer { line-height:1.5; }
.st-key-top-nav [data-testid="stButton"] button { border:0; background:transparent; padding:.2rem .4rem; font-family:'DM Mono',monospace; letter-spacing:.15em; font-size:.72rem; }
.st-key-top-nav [data-testid="stButton"] button:hover { color:var(--signal); border:0; }
.start-door [data-testid="stButton"] button { width:100%; min-height:5.2rem; border-radius:50%; background:#111; color:white; border:0; font-family:'DM Mono',monospace; letter-spacing:.08em; font-size:.76rem; }
.start-door [data-testid="stButton"] button:hover { background:var(--signal); color:white; border:0; }
[data-testid="stDialog"],[role="dialog"] { background:#0d0f14!important; color:#f5f5f2!important; }
[data-testid="stDialog"]>div,[role="dialog"]>div { padding-left:clamp(1rem,4vw,2.25rem)!important; padding-right:clamp(1rem,4vw,2.25rem)!important; }
[data-testid="stDialog"] h1,[data-testid="stDialog"] h2,[data-testid="stDialog"] h3,[data-testid="stDialog"] p,[data-testid="stDialog"] strong,[data-testid="stDialog"] label,[data-testid="stDialog"] [data-testid="stCaptionContainer"] { color:#f5f5f2!important; background:transparent!important; }
[data-testid="stDialog"] [data-testid="stCaptionContainer"],[data-testid="stDialog"] small { color:#858894!important; }
[data-testid="stDialog"] label { min-height:1.4rem; font-size:1rem!important; font-weight:500; }
[data-testid="stDialog"] [data-baseweb="input"],[data-testid="stDialog"] [data-baseweb="textarea"],[data-testid="stDialog"] [data-baseweb="select"]>div { border:1px solid #434753!important; border-radius:.25rem!important; background:#171a21!important; box-shadow:none!important; }
[data-testid="stDialog"] input,[data-testid="stDialog"] textarea { min-height:44px; background:#171a21!important; color:#f5f5f2!important; caret-color:#f5f5f2; font-size:16px!important; }
[data-testid="stDialog"] textarea { min-height:9rem; }
[data-testid="stDialog"] input::placeholder,[data-testid="stDialog"] textarea::placeholder { color:#858894!important; opacity:1; }
[data-testid="stDialog"] [data-baseweb="input"]:focus-within,[data-testid="stDialog"] [data-baseweb="textarea"]:focus-within,[data-testid="stDialog"] [data-baseweb="select"]>div:focus-within { border-color:#f5f5f2!important; box-shadow:0 0 0 2px rgba(49,95,120,.8)!important; }
[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] { min-height:7rem; border:1px dashed #858894!important; background:#171a21!important; color:#f5f5f2!important; }
[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] * { color:#b9bbc2!important; background:transparent!important; }
[data-testid="stDialog"] button { min-height:44px; border-color:#858894; background:transparent; color:#f5f5f2; font-family:'DM Mono',monospace; font-size:16px!important; }
[data-testid="stDialog"] [data-testid="stButton"] button p,[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button p { color:#fafafa!important; }
[data-testid="stDialog"] button[kind="primary"] { border-color:#f5f5f2!important; background:#f5f5f2!important; color:#0d0f14!important; font-weight:600; }
[data-testid="stDialog"] button[kind="primary"] p { color:#0d0f14!important; }
[data-testid="stDialog"] button:hover,[data-testid="stDialog"] button:focus-visible { border-color:#f5f5f2; background:rgba(245,245,242,.1); color:#fff; outline:2px solid #315f78; outline-offset:2px; }
[data-testid="stDialog"] button:hover p,[data-testid="stDialog"] button:focus-visible p { color:#fff!important; }
[data-testid="stDialog"] button:disabled { border-color:#434753; background:#171a21!important; color:#858894; opacity:.62; }
[data-testid="stDialog"] button:disabled p { color:#fafafa!important; }
.door-option { border-top:1px solid rgba(17,17,17,.18); padding:.9rem 0 .3rem; font-family:'DM Mono',monospace; }
.door-dormant { opacity:.36; }
.entry-flow { margin:1rem 0 2rem; padding:.8rem 0; border-top:1px solid currentColor; border-bottom:1px solid currentColor; font-family:'DM Mono',monospace; font-size:.7rem; letter-spacing:.08em; }
.entry-question { margin:2rem 0 1rem; font-family:'DM Mono',monospace; font-size:clamp(1.5rem,3vw,2.6rem); font-weight:500; letter-spacing:.08em; }
.entry-selected { margin:1.5rem 0; padding:1rem 0; border-top:1px solid currentColor; border-bottom:1px solid currentColor; font-family:'DM Mono',monospace; }
.entry-selected small,.entry-selected strong { display:block; }.entry-selected small{opacity:.6;font-size:.6rem;letter-spacing:.14em}.entry-selected strong{margin-top:.5rem;font-size:1.3rem;letter-spacing:.08em}
.entry-auth { margin:2rem 0 1rem; padding:1.2rem 0; border-top:2px solid currentColor; font-family:'DM Mono',monospace; }.entry-auth small,.entry-auth strong{display:block}.entry-auth small{font-size:.62rem;letter-spacing:.14em}.entry-auth strong{margin:.8rem 0;font-size:1.1rem;letter-spacing:.06em}.entry-auth p{font-size:.72rem;line-height:1.5}
.section-head { margin:4rem 0 2rem; font-family:'DM Mono',monospace; font-size:clamp(2.625rem,3.2vw,3rem); line-height:1; letter-spacing:.12em; }
.timeline-phase { margin:-1.2rem 0 2.5rem; font-family:'DM Mono',monospace; font-size:.72rem; font-weight:500; letter-spacing:.12em; }
.analysis-head { margin:3rem 0 1rem; padding-top:1rem; border-top:1px solid rgba(17,17,17,.2); font-family:'DM Mono',monospace; font-size:.72rem; font-weight:500; letter-spacing:.14em; }
.dataset-label { margin:1.5rem 0 .5rem; font-family:'DM Mono',monospace; font-size:.65rem; letter-spacing:.12em; color:var(--muted); }
.necessity { display:grid; grid-template-columns:minmax(11rem,1fr) minmax(9rem,.55fr) minmax(9rem,.55fr); gap:1.2rem; padding:1.1rem 0; border-top:1px solid rgba(17,17,17,.22); font-family:'DM Mono',monospace; font-size:.78rem; }
.necessity .status { text-transform:uppercase; letter-spacing:.08em; }
.necessity .stage { color:var(--muted); text-transform:uppercase; }
.necessity-head { padding:.45rem 0; color:var(--muted); font-size:.5625rem; letter-spacing:.14em; }
.necessity.dormant { opacity:.38; }
.node-kind { font-family:'DM Mono',monospace; color:var(--signal); text-transform:uppercase; letter-spacing:.13em; font-size:.73rem; }
.relation-role { margin:1rem 0; padding:1rem 0; border-top:1px solid rgba(17,17,17,.2); border-bottom:1px solid rgba(17,17,17,.2); font-family:'DM Mono',monospace; font-size:1.5rem; letter-spacing:.12em; }
.node-population-stage { margin:1.2rem 0; padding:.8rem 0; border-top:2px solid currentColor; border-bottom:1px solid currentColor; font-family:'DM Mono',monospace; font-size:.72rem; font-weight:500; letter-spacing:.14em; }
.node-preview-label { margin:1rem 0 .5rem; color:#858894; font-family:'DM Mono',monospace; font-size:.75rem; letter-spacing:.12em; }
.inhabited-node-avatar { width:min(13rem,42vw); aspect-ratio:1; margin:1rem auto 2rem; border:1px solid currentColor; border-radius:50%; background-color:#151515; background-repeat:no-repeat; }
.inhabited-node-practice { display:flex; flex-wrap:wrap; gap:.45rem; margin:1.4rem 0; }.inhabited-node-practice span { padding:.38rem .65rem; border:1px solid currentColor; border-radius:999px; font-family:'DM Mono',monospace; font-size:.65rem; letter-spacing:.06em; }
.inhabited-node-sample { margin:1.4rem 0; padding:1rem 0; border-top:1px solid currentColor; border-bottom:1px solid currentColor; font-family:'DM Mono',monospace; }.inhabited-node-sample small,.inhabited-node-sample strong,.inhabited-node-sample span,.inhabited-node-sample a{display:block}.inhabited-node-sample small{font-size:.6rem;letter-spacing:.13em}.inhabited-node-sample strong{margin:.7rem 0;font-size:1rem}.inhabited-node-sample span,.inhabited-node-sample a{overflow-wrap:anywhere;font-size:.62rem;opacity:.75;color:inherit}
[class*="st-key-activation-drop-"] { margin:2rem 0; padding:1rem; border:2px solid #111; }
.activation-drop-head { display:flex; align-items:baseline; justify-content:space-between; gap:1rem; font-family:'DM Mono',monospace; }.activation-drop-head small{font-size:.6rem;letter-spacing:.13em}.activation-drop-head strong{font-size:1.1rem;letter-spacing:.1em}
.state-dialog-stats { display:grid; grid-template-columns:1fr 1fr; gap:.5rem 1.5rem; margin:1.5rem 0 2rem; padding:1rem 0; border-top:1px solid #111; border-bottom:1px solid #111; font-family:'DM Mono',monospace; font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; }
.application-transition { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:1rem; margin:1.5rem 0 2rem; padding:1rem; border:1px solid #111; font-family:'DM Mono',monospace; font-size:.72rem; letter-spacing:.08em; }
.application-transition span:last-child { opacity:.35; }.application-transition span.submitted { opacity:1; }
.st-key-resource-actions { margin:2rem 0 2.5rem; padding:1.2rem 0; border-top:2px solid #111; border-bottom:2px solid #111; }
.st-key-resource-actions [data-testid="stButton"] button { min-height:4rem; border:1px solid #111; border-radius:0; background:#111; color:#fff; font-family:'DM Mono',monospace; font-size:clamp(.82rem,1.1vw,1.05rem); font-weight:700; letter-spacing:.12em; }
.st-key-resource-actions [data-testid="stButton"] button:hover { border-color:var(--signal); background:var(--signal); color:#fff; }
.resource-action-explanation { min-height:3.4rem; margin:.65rem 0 0; font-family:'DM Mono',monospace; font-size:.63rem; line-height:1.45; }
.order-art-empty { margin:3rem 0; padding:clamp(2rem,6vw,5rem) 0; border-top:2px solid #111; border-bottom:2px solid #111; }
.order-art-empty small,.order-art-empty strong { display:block; font-family:'DM Mono',monospace; }
.order-art-empty small { margin-bottom:2rem; color:var(--muted); font-size:.65rem; letter-spacing:.14em; }
.order-art-empty strong { max-width:52rem; font-size:clamp(2rem,5vw,5rem); line-height:1; letter-spacing:-.04em; }
.takeover-footer { display:block; margin:clamp(2.5rem,7vh,5rem) 0 0; padding:1.1rem 0 0; border-top:1px solid rgba(17,17,17,.24); font-family:'DM Mono',monospace; }
.takeover-footer>span { color:var(--muted); font-size:.62rem; letter-spacing:.16em; }
.takeover-footer nav { display:grid; grid-template-columns:1fr; gap:.55rem; margin-top:.8rem; }
.takeover-footer a { display:grid; grid-template-columns:2.2rem auto; grid-template-rows:auto auto; min-width:0; padding:.7rem .8rem; border:1px solid #111; color:#111!important; text-decoration:none!important; transition:background .16s ease,color .16s ease,transform .16s ease; }
.takeover-footer a:hover { background:#111; color:#fff!important; transform:translateY(-2px); }
.takeover-footer svg { grid-row:1 / 3; width:1.6rem; height:1.6rem; align-self:center; fill:currentColor; }
.takeover-footer strong { font-size:.72rem; letter-spacing:.12em; }.takeover-footer small { margin-top:.16rem; opacity:.62; font-size:.55rem; letter-spacing:.08em; }
.resource-field-row { display:grid; grid-template-columns:8rem minmax(6rem,1fr) minmax(10rem,.7fr); gap:.5rem 1rem; align-items:center; padding:.72rem 0; border-top:1px solid rgba(17,17,17,.18); font-family:'DM Mono',monospace; }
.resource-field-row strong,.resource-field-row span { font-size:.72rem; letter-spacing:.08em; }.resource-field-row span { text-align:right; }
.resource-field-row i { height:.48rem; background:repeating-linear-gradient(90deg,#111 0 10%,transparent 10% 12%); opacity:.2; }
.resource-field-row.state-secured i { opacity:.9; }.resource-field-row.state-offered i,.resource-field-row.state-intention i { opacity:.45; }.resource-field-row.state-growing i { background:linear-gradient(90deg,#111,transparent); opacity:.8; }
.resource-field-row small { grid-column:2 / 4; color:var(--muted); font-size:.56rem; letter-spacing:.04em; }
.i18n-lab { max-width:980px; margin:clamp(4rem,9vh,8rem) auto 0; }
.i18n-eyebrow,.i18n-locale,.i18n-foot { font-family:'DM Mono',monospace; letter-spacing:.16em; font-size:.68rem; color:var(--muted); }
.i18n-eyebrow { text-align:center; margin-bottom:1.2rem; }
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
.voices-head h1 { margin:0!important; font-size:clamp(2.625rem,3.2vw,3rem)!important; }
.voices-head p { max-width:28rem; color:var(--muted); font-family:'DM Mono',monospace; font-size:.75rem; line-height:1.6; }
.st-key-voices-language-rail { max-width:760px; margin:-2rem auto 4.5rem; padding:.4rem; border:1px solid rgba(17,17,17,.14); border-radius:2.4rem; background:rgba(255,255,255,.46); }
.st-key-voices-language-rail [data-testid="stHorizontalBlock"] { gap:.25rem; }
.st-key-voices-language-rail [data-testid="stHorizontalBlock"] + [data-testid="stHorizontalBlock"] { margin-top:.25rem; }
.st-key-voices-language-rail [data-testid="stButton"] button { min-height:2.8rem; padding:.3rem .5rem; border:0; border-radius:999px; background:transparent; font-family:'DM Mono',monospace; font-size:.72rem; letter-spacing:.04em; }
.st-key-voices-language-rail [data-testid="stButton"] button:hover { border:0; background:rgba(49,95,120,.1); color:var(--signal); }
.st-key-voices-language-rail [data-testid="stButton"] button[kind="primary"] { border:0; background:var(--signal); color:#fff; }
.st-key-voices-language-rail [data-testid="stButton"] button[kind="primary"] p { color:#fff!important; }
.voice-contribution-key { display:flex; align-items:center; gap:.8rem; margin:-2.2rem 0 3rem; padding:1rem 0; border-top:1px solid rgba(17,17,17,.18); border-bottom:1px solid rgba(17,17,17,.18); font-family:'DM Mono',monospace; }
.voice-contribution-key span { display:grid; place-items:center; width:2.2rem; height:2.2rem; border-radius:50%; background:#111; color:#fff; }
.voice-contribution-key strong { margin-right:1rem; font-size:.72rem; letter-spacing:.11em; }.voice-contribution-key small { margin-left:auto; color:var(--muted); font-size:.65rem; }
.language-status-title { margin:0 0 1rem; font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.14em; color:var(--muted); }
.voice-stat { min-height:6.8rem; margin-bottom:2rem; padding:1rem; border-top:1px solid rgba(17,17,17,.2); font-family:'DM Mono',monospace; }
.voice-stat small,.voice-stat strong,.voice-stat span { display:block; }
.voice-stat small { min-height:2rem; color:var(--muted); font-size:.6rem; letter-spacing:.08em; }
.voice-stat strong { font-size:1.35rem; font-weight:400; }
.voice-stat span { margin-top:.35rem; font-size:.65rem; color:var(--muted); }
.language-metric { min-height:6.4rem; margin-bottom:1rem; padding:.8rem; border-top:1px solid rgba(17,17,17,.18); font-family:'DM Mono',monospace; }
.language-metric strong { display:block; margin-bottom:.65rem; font-size:.67rem; letter-spacing:.06em; }
.language-metric small { display:block; margin-top:.55rem; color:var(--muted); font-size:.55rem; line-height:1.4; }
.status-bar { display:flex; width:100%; height:.38rem; overflow:hidden; border-radius:999px; background:#d9d5cf; }
.status-bar i { display:block; height:100%; }.status-canonical{background:#111}.status-provisional{background:#315f78}.status-untranslated{background:#d9d5cf}
.persona-kicker { margin:4rem 0 .8rem; text-align:center; color:var(--muted); font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.2em; }
.persona-emoji { margin:0 auto 1rem; padding:2rem 0; border-top:1px solid #111; border-bottom:1px solid #111; text-align:center; font-size:clamp(4rem,14vw,8rem); line-height:1.1; letter-spacing:.08em; }
[class*="st-key-record-voice-"] { display:flex; justify-content:flex-end; padding-top:1.7rem; }
[class*="st-key-record-voice-"] [data-testid="stButton"] button { width:2.5rem; min-height:2.5rem; padding:0; border:1px solid #111; border-radius:50%; background:#111; color:#fff; }
[class*="st-key-record-voice-"] [data-testid="stButton"] button:hover { border-color:var(--signal); background:var(--signal); color:#fff; }
[class*="st-key-record-voice-"] [data-testid="stButton"] button p { color:#fff!important; }
[data-baseweb="tooltip"],[data-testid="stTooltipContent"] { width:max-content!important; max-width:min(22rem,calc(100vw - 2rem))!important; padding:.45rem .65rem!important; border-radius:.35rem!important; background:#111!important; color:var(--paper)!important; font-family:'DM Mono',monospace!important; font-size:.65rem!important; line-height:1.3!important; letter-spacing:.06em!important; white-space:normal!important; }
[data-baseweb="tooltip"] *,[data-testid="stTooltipContent"] * { color:var(--paper)!important; }
[class*="st-key-add-translation-"] { display:flex; justify-content:flex-end; padding-top:1.7rem; }
[class*="st-key-add-translation-"] [data-testid="stButton"] button { width:2.5rem; min-height:2.5rem; padding:0; border:1px solid #315f78; border-radius:50%; background:transparent; color:#315f78; font-family:'DM Mono',monospace; font-size:1.15rem; }
[class*="st-key-add-translation-"] [data-testid="stButton"] button:hover { border-color:#315f78; background:#315f78; color:#fff; }
.translation-source,.translation-current { margin:.35rem 0 1.4rem; padding:.8rem 0; border-top:1px solid rgba(17,17,17,.18); font-family:'DM Mono',monospace; font-size:1rem; }
.translation-current { color:var(--muted); }
.recording-utterance { margin-bottom:1.5rem; font-family:'DM Mono',monospace; font-size:1.4rem; line-height:1.2; }
.voice { position:relative; padding:2rem 0 2.4rem; border-top:1px solid rgba(17,17,17,.18); }
.voice-meta { display:block; margin-bottom:.9rem; color:var(--muted); font-family:'DM Mono',monospace; letter-spacing:.09em; text-transform:uppercase; }
.voice-phrase { max-width:900px; font-family:'DM Mono',monospace; line-height:1.04; letter-spacing:.02em; }
.voice-weight-1 { font-size:.9rem; }
.voice-weight-2 { font-size:1.15rem; }
.voice-weight-3 { font-size:1.65rem; }
.voice-weight-4 { font-size:2.5rem; }
.voice-weight-5 { font-size:4.2rem; }
.voice-versions { display:grid; grid-template-columns:repeat(auto-fit,minmax(10rem,1fr)); gap:1rem; max-height:0; overflow:hidden; opacity:0; transition:max-height .25s ease,opacity .25s ease; }
.voice:hover .voice-versions,.voice:focus-within .voice-versions { max-height:24rem; margin-top:1.6rem; opacity:1; }
.voice-versions span { color:var(--muted); font-size:.72rem; line-height:1.45; }
.voice-versions b { display:block; margin-bottom:.35rem; color:var(--ink); font-family:'DM Mono',monospace; letter-spacing:.14em; }
.voice button { margin-top:1rem; padding:0; border:0; background:transparent; color:#77736e; font-family:'DM Mono',monospace; font-size:.62rem; letter-spacing:.12em; }
.voice small { margin-left:1rem; color:#aaa6a0; font-family:'DM Mono',monospace; font-size:.6rem; }
@media(max-width:850px){ .block-container{padding:1.2rem}.takeover-copy{padding-top:3rem}.takeover-three-blocks{grid-template-columns:1fr}.necessity{grid-template-columns:1fr 1fr}.listening{display:block}.listening span{display:block;margin-top:.5rem}.listening-item{display:block}.listening-item h3{margin:.6rem 0!important}.listening-item span,.listening-item footer{display:block;margin-top:.45rem} }
@media(max-width:850px){ .application-file-action{min-height:142px;margin:2rem 0 1rem;padding:1.7rem 12%;grid-template-columns:1.7rem 1fr auto}.application-file-action svg{width:1.6rem;height:1.6rem} }
@media(max-width:850px){ .takeover-footer{display:block}.takeover-footer nav{margin-top:1rem;flex-direction:column}.takeover-footer a{min-width:0} }
@media(max-width:850px){ .voices-head{display:block}.voice-versions{grid-template-columns:1fr 1fr}.voice:hover .voice-versions{max-height:24rem} }
</style>
"""
