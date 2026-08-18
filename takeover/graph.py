"""Self-contained, read-only multiplex graph presentation."""

from __future__ import annotations

import html
import json
from math import cos, pi, sin
import secrets
from urllib.parse import quote

from .models import Entity, Relation


def build_graph_html(
    entities: list[Entity],
    relations: list[Relation],
    start_label: str = "START HERE",
    you_label: str = "YOU?",
    invitation: str = "Bring your voice, your image, your practice.",
    nodes_label: str = "NODES",
    connections_label: str = "CONNECTIONS",
    ratio_label: str = "CONNECTIONS/NODE",
) -> str:
    width, height = 920, 590
    centre = (width / 2, height / 2)
    positions: dict[str, tuple[float, float]] = {}
    for index, entity in enumerate(entities):
        angle = -pi / 2 + (2 * pi * index / max(1, len(entities)))
        radius = 205 + (index % 3) * 22
        positions[entity.id] = (centre[0] + cos(angle) * radius, centre[1] + sin(angle) * radius)
    lines = []
    for relation in relations:
        if relation.source in positions and relation.target in positions:
            x1, y1 = positions[relation.source]
            x2, y2 = positions[relation.target]
            lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="relation"><title>{html.escape(relation.type)}</title></line>')
    nodes = []
    kind_class = {"person": "person", "photograph": "photograph", "audio": "audio"}
    for index, entity in enumerate(entities):
        x, y = positions[entity.id]
        query = quote(entity.id, safe="")
        label = html.escape(entity.title)
        kind = kind_class[entity.type]
        nodes.append(
            f'<a href="?view=network&amp;node={query}" target="_top" class="node {kind}" '
            f'style="left:{x:.1f}px;top:{y:.1f}px;--delay:-{index * .37:.2f}s" aria-label="Inspect {label}">'
            f'<span class="orb"></span><strong>{label}</strong><small>{html.escape(entity.label or entity.type)}</small></a>'
        )
    count = len(entities)
    connection_count = len(lines)
    ratio = f"{connection_count / count:.3f}" if count else f"{secrets.randbelow(9_000_000_000_000) + 1_000_000_000_000:.11E}"
    payload = json.dumps({"nodes": count, "connections": len(lines)})
    ghost_points = [(112, 112), (215, 78), (325, 150), (450, 76), (565, 128), (710, 82), (824, 165), (785, 292), (842, 420), (710, 490), (590, 445), (476, 520), (345, 460), (205, 515), (96, 405), (158, 295)]
    ghost_edges = [(0, 2), (1, 2), (2, 3), (2, 5), (3, 4), (4, 6), (5, 7), (6, 7), (7, 8), (7, 10), (8, 9), (9, 10), (9, 11), (10, 12), (11, 13), (12, 13), (12, 14), (13, 15), (14, 15), (0, 15), (2, 15), (4, 10)]
    ghosts = ''.join(f'<circle class="ghost" cx="{x}" cy="{y}" r="3.5"/>' for x, y in ghost_points)
    ghost_lines = ''.join(f'<line class="latent" x1="{ghost_points[a][0]}" y1="{ghost_points[a][1]}" x2="{ghost_points[b][0]}" y2="{ghost_points[b][1]}"/>' for a, b in ghost_edges)
    return f"""
    <style>
      * {{ box-sizing: border-box; }}
      body {{ margin:0; background:transparent; color:#111; font-family:'Courier New',monospace; }}
      .field {{ position:relative; width:100%; max-width:{width}px; height:{height}px; margin:auto; overflow:hidden; }}
      svg {{ position:absolute; inset:0; width:100%; height:100%; }}
      .relation {{ stroke:#111; stroke-width:2.4; opacity:.76; }}
      .ghost {{ fill:#aaa6a0; opacity:.34; }}
      .latent {{ stroke:#aaa6a0; stroke-width:.55; opacity:.22; }}
      .hub {{ position:absolute; left:50%; top:43%; transform:translate(-50%,-50%); display:grid; place-items:center;
        width:96px; height:96px; border-radius:50%; background:#111; color:#fff; font-size:38px; text-decoration:none; }}
      .hub:hover,.hub:focus {{ background:#123dff; outline:0; }}
      .hub-label {{ position:absolute; left:50%; top:calc(43% + 58px); transform:translateX(-50%); font-size:12px; letter-spacing:.11em; white-space:nowrap; }}
      .you {{ position:absolute; left:50%; top:76%; transform:translate(-50%,-50%); width:190px; text-align:center; }}
      .you-orb {{ display:grid; place-items:center; width:76px; height:76px; margin:auto; border:1px solid #8d8983; border-radius:50%; background:rgba(255,255,255,.25); font-size:30px; color:#595652; }}
      .you strong {{ display:block; margin-top:10px; font-size:12px; letter-spacing:.13em; }}
      .you small {{ display:block; margin-top:5px; line-height:1.4; color:#68635e; }}
      .empty {{ position:absolute; left:7%; bottom:8%; color:#8b8781; font-size:10px; letter-spacing:.12em; }}
      .node {{ position:absolute; transform:translate(-50%,-50%); width:132px; color:#111; text-decoration:none; text-align:center;
        animation:wobble 6s ease-in-out infinite alternate; animation-delay:var(--delay); }}
      .orb {{ display:block; width:92px; height:92px; margin:0 auto 10px; border-radius:50%; border:1px solid #111; background:#d6d3ce; }}
      .person .orb {{ background:#151515; }}
      .photograph .orb {{ background:radial-gradient(circle at 35% 35%,#f4f1ec 0 8%,#74736f 9% 42%,#171717 43%); }}
      .audio .orb {{ background:repeating-radial-gradient(circle,#171717 0 3px,#e4e0da 4px 8px); }}
      .node strong,.node small {{ display:block; }}
      .node strong {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; }}
      .node small {{ margin-top:3px; font-size:10px; color:#64615e; }}
      .stats {{ position:absolute; right:18px; bottom:18px; display:grid; grid-template-columns:auto minmax(8rem,auto); gap:.15rem 1.4rem; font-size:10px; letter-spacing:.12em; line-height:1.7; text-transform:uppercase; }}
      .stats b {{ text-align:right; font-weight:400; }}
      @keyframes wobble {{ from {{ transform:translate(-50%,-50%) rotate(-1.2deg) translateY(-3px); }} to {{ transform:translate(-50%,-50%) rotate(1.2deg) translateY(4px); }} }}
      @media (prefers-reduced-motion:reduce) {{ .node {{ animation:none; }} }}
    </style>
    <div class="field" data-registry='{html.escape(payload)}'>
      <svg viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
        {ghost_lines}{ghosts}{''.join(lines)}
      </svg>
      <a class="hub" href="?view=network&amp;door=access" target="_top" aria-label="{html.escape(start_label)}">+</a><div class="hub-label">{html.escape(start_label)}</div>
      <div class="you"><span class="you-orb">+</span><strong>{html.escape(you_label)}</strong><small>{html.escape(invitation)}</small></div>
      {''.join(nodes)}
      <div class="stats"><span>{html.escape(nodes_label)}</span><b>{count}</b><span>{html.escape(connections_label)}</span><b>{connection_count}</b><span>{html.escape(ratio_label)}</span><b>{ratio}</b></div>
    </div>
    """
