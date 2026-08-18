"""Self-contained, read-only multiplex graph presentation."""

from __future__ import annotations

import html
import json
from math import cos, pi, sin
from urllib.parse import quote

from .models import Entity, Relation


def build_graph_html(entities: list[Entity], relations: list[Relation]) -> str:
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
    payload = json.dumps({"nodes": count, "connections": len(lines)})
    return f"""
    <style>
      * {{ box-sizing: border-box; }}
      body {{ margin:0; background:transparent; color:#111; font-family:'Courier New',monospace; }}
      .field {{ position:relative; width:100%; max-width:{width}px; height:{height}px; margin:auto; overflow:hidden; }}
      svg {{ position:absolute; inset:0; width:100%; height:100%; }}
      .relation {{ stroke:#111; stroke-width:2.4; opacity:.76; }}
      .ghost {{ fill:#111; opacity:.12; }}
      .hub {{ position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); display:grid; place-items:center;
        width:90px; height:90px; border-radius:50%; background:#111; color:#fff; font-size:34px; }}
      .hub-label {{ position:absolute; left:50%; top:calc(50% + 58px); transform:translateX(-50%); font-size:12px; letter-spacing:.11em; white-space:nowrap; }}
      .node {{ position:absolute; transform:translate(-50%,-50%); width:132px; color:#111; text-decoration:none; text-align:center;
        animation:wobble 6s ease-in-out infinite alternate; animation-delay:var(--delay); }}
      .orb {{ display:block; width:92px; height:92px; margin:0 auto 10px; border-radius:50%; border:1px solid #111; background:#d6d3ce; }}
      .person .orb {{ background:#151515; }}
      .photograph .orb {{ background:radial-gradient(circle at 35% 35%,#f4f1ec 0 8%,#74736f 9% 42%,#171717 43%); }}
      .audio .orb {{ background:repeating-radial-gradient(circle,#171717 0 3px,#e4e0da 4px 8px); }}
      .node strong,.node small {{ display:block; }}
      .node strong {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; }}
      .node small {{ margin-top:3px; font-size:10px; color:#64615e; }}
      .stats {{ position:absolute; right:18px; bottom:18px; font-size:10px; letter-spacing:.12em; line-height:1.9; text-transform:uppercase; }}
      @keyframes wobble {{ from {{ transform:translate(-50%,-50%) rotate(-1.2deg) translateY(-3px); }} to {{ transform:translate(-50%,-50%) rotate(1.2deg) translateY(4px); }} }}
      @media (prefers-reduced-motion:reduce) {{ .node {{ animation:none; }} }}
    </style>
    <div class="field" data-registry='{html.escape(payload)}'>
      <svg viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
        {''.join(lines)}
        <circle class="ghost" cx="170" cy="145" r="4"/><circle class="ghost" cx="745" cy="120" r="4"/>
        <circle class="ghost" cx="770" cy="455" r="4"/><circle class="ghost" cx="140" cy="465" r="4"/>
      </svg>
      <div class="hub">+</div><div class="hub-label">START HERE</div>
      {''.join(nodes)}
      <div class="stats">{count} nodes<br>{len(lines)} connections</div>
    </div>
    """

