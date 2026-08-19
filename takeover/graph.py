"""Self-contained, read-only multiplex graph presentation."""

from __future__ import annotations

import html
import json
from math import atan2, degrees, hypot
from urllib.parse import quote

from .models import Entity, Relation, entity_type_label


def clipped_segment(
    source: tuple[float, float],
    target: tuple[float, float],
    source_radius: float,
    target_radius: float,
) -> tuple[float, float, float, float]:
    """Return an edge clipped to the circumferences of two circular nodes."""
    dx = target[0] - source[0]
    dy = target[1] - source[1]
    distance = hypot(dx, dy)
    if distance <= source_radius + target_radius:
        raise ValueError("Connected nodes must not overlap.")
    ux, uy = dx / distance, dy / distance
    return (
        source[0] + source_radius * ux,
        source[1] + source_radius * uy,
        target[0] - target_radius * ux,
        target[1] - target_radius * uy,
    )


def build_graph_html(
    entities: list[Entity],
    relations: list[Relation],
    start_label: str = "START HERE",
    state_label: str = "STATE OF THE ART",
    nodes_label: str = "NODES",
    connections_label: str = "CONNECTIONS",
    ratio_label: str = "CONNECTIVITY",
    relations_label: str = "ACTIVE RELATIONS",
    forthcoming_label: str = "+ ADD NODE · + ADD CONNECTION / OPENING NEXT",
    active_label: str = "ACTIVE",
    latent_known_label: str = "LATENT KNOWN",
    latent_private_label: str = "LATENT PRIVATE",
    unknown_label: str = "UNKNOWN",
) -> str:
    width, height = 920, 590
    # Stable normalized graph coordinates. Topology and relative placement do
    # not change with viewport size; the entire field scales as one geometry.
    semantic_positions = {
        "kumiori": (.12, .48),
        "ave": (.43, .16),
        "mai_brit": (.68, .50),
        "kenneerik": (.28, .78),
        "graziano": (.83, .16),
        "michela": (.10, .20),
        "latent_01": (.86, .78),
        "latent_02": (.08, .84),
    }
    fallback_positions = ((.28, .25), (.72, .28), (.73, .68), (.27, .70), (.85, .42), (.14, .48))
    positions: dict[str, tuple[float, float]] = {}
    for index, entity in enumerate(entities):
        px, py = semantic_positions.get(entity.id, fallback_positions[index % len(fallback_positions)])
        positions[entity.id] = (px * width, py * height)

    entity_status = {entity.id: entity.status for entity in entities}
    lines: list[str] = []
    for relation in relations:
        active_edge = (
            relation.source in positions
            and relation.target in positions
            and entity_status.get(relation.source) == "active"
            and entity_status.get(relation.target) == "active"
        )
        if not active_edge:
            continue
        x1, y1, x2, y2 = clipped_segment(
            positions[relation.source], positions[relation.target], 44, 44
        )
        length = hypot(x2 - x1, y2 - y1)
        angle = degrees(atan2(y2 - y1, x2 - x1))
        query = quote(relation.id, safe="")
        relation_label = html.escape(relation.type)
        lines.append(
            f'<a href="?view=network&amp;relation={query}" class="relation-link" '
            f'style="left:{100 * x1 / width:.4f}%;top:{100 * y1 / height:.4f}%;'
            f'width:{100 * length / width:.4f}%;--angle:{angle:.4f}deg" '
            f'aria-label="Inspect {relation_label} relation"><span class="relation-stroke"></span>'
            f'<span class="relation-marker"></span></a>'
        )

    nodes: list[str] = []
    kind_class = {"person": "person", "photograph": "photograph", "audio": "audio"}
    for index, entity in enumerate(entities):
        x, y = positions[entity.id]
        label = html.escape(entity.title)
        kind = kind_class[entity.type]
        depth = int(entity.metadata.get("depth", 0))
        state_class = entity.status.replace("_", "-")
        label_parts = [part.strip() for part in entity.label.split("/")]
        if entity.type == "person":
            if label_parts and label_parts[0].lower().replace(" ", "") in {"person•alien", "person·alien"}:
                label_parts[0] = entity_type_label(entity.type)
            else:
                label_parts.insert(0, entity_type_label(entity.type))
        context = " · ".join(label_parts) if label_parts else entity_type_label(entity.type)
        style = f'left:{100 * x / width:.2f}%;top:{100 * y / height:.2f}%;--delay:-{index * .37:.2f}s;--depth:{depth}'
        if entity.status == "active":
            display_name = str(entity.metadata.get("display_name") or "").strip()
            if display_name:
                context = f"{display_name} · {context}"
            query = quote(entity.id, safe="")
            nodes.append(
                f'<a href="?view=network&amp;node={query}" class="node active {kind}" '
                f'style="{style}" aria-label="Inspect {label}">'
                f'<span class="orb"></span><strong>{label}<i> ↗</i></strong><small>{html.escape(context)}</small></a>'
            )
        else:
            visible_label = label if entity.status == "latent_known" else ""
            aria = f' aria-label="{label}, {html.escape(entity.status)}"' if visible_label else ' aria-hidden="true"'
            nodes.append(
                f'<div class="node depth-node {state_class} {kind}" style="{style}"{aria}>'
                f'<span class="orb"></span>{f"<strong>{visible_label}</strong>" if visible_label else ""}</div>'
            )

    state_counts = {
        status: sum(entity.status == status for entity in entities)
        for status in ("active", "latent_known", "latent_private", "unknown")
    }
    connection_count = len(lines)
    count = len(entities)
    ratio = f"{(1 + connection_count) / count:.2f}" if count else "0.00"
    active_relation_count = sum(
        relation.status == "active"
        and entity_status.get(relation.source) == "active"
        and entity_status.get(relation.target) == "active"
        for relation in relations
    )
    payload = json.dumps({"nodes": count, "connections": connection_count, "states": state_counts})

    return f"""
    <style>
      * {{ box-sizing:border-box; }}
      body {{ margin:0; background:transparent; color:#111; font-family:'Courier New',monospace; }}
      .field {{ position:relative; width:100%; max-width:{width}px; aspect-ratio:{width}/{height}; margin:auto; overflow:hidden; }}
      .relation-link {{ position:absolute; z-index:2; height:3.05%; transform:translateY(-50%) rotate(var(--angle)); transform-origin:0 50%; cursor:pointer; }}
      .relation-stroke {{ position:absolute; left:0; right:0; top:calc(50% - 1px); height:2px; background:#111; opacity:.68; transition:height .16s ease,top .16s ease,opacity .16s ease; }}
      .relation-marker {{ position:absolute; left:50%; top:50%; width:7px; height:7px; transform:translate(-50%,-50%); border:1px solid #111; border-radius:50%; background:#f5f2ed; transition:width .16s ease,height .16s ease,background .16s ease; }}
      .relation-link:hover .relation-stroke,.relation-link:focus .relation-stroke {{ top:calc(50% - 2px); height:4px; opacity:1; }}
      .relation-link:hover .relation-marker,.relation-link:focus .relation-marker {{ width:15px; height:15px; background:#111; }}
      .hub {{ position:absolute; z-index:4; left:45%; top:50%; transform:translate(-50%,-50%); display:grid; place-items:center;
        width:8.91%; aspect-ratio:1; border-radius:50%; background:#111; color:#fff; font-size:clamp(22px,2.5vw,34px); text-decoration:none; }}
      .hub:hover,.hub:focus {{ background:#777168; outline:0; }}
      .hub-label {{ position:absolute; z-index:4; left:45%; top:59%; transform:translateX(-50%); font-size:10px; letter-spacing:.11em; white-space:nowrap; }}
      .node {{ position:absolute; z-index:3; transform:translate(-50%,-50%); width:15%; color:#111; text-decoration:none; text-align:center;
        animation:wobble 6s ease-in-out infinite alternate; animation-delay:var(--delay); }}
      .orb {{ display:block; width:63.77%; aspect-ratio:1; margin:0 auto 9px; border-radius:50%; border:1px solid #45413d; background:#151515; box-shadow:inset 0 0 0 1px rgba(255,255,255,.16); transition:transform .16s ease,box-shadow .16s ease; }}
      .node strong,.node small {{ display:block; }}
      .node strong {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; }}
      .node small {{ margin-top:3px; font-size:9px; color:#64615e; }}
      .node i {{ opacity:0; font-style:normal; transition:opacity .16s ease; }}
      .active:hover .orb,.active:focus .orb {{ transform:scale(1.045); box-shadow:inset 0 0 0 1px rgba(255,255,255,.28),0 0 0 3px rgba(17,17,17,.12); }}
      .active:hover i,.active:focus i {{ opacity:1; }}
      .photograph .orb {{ background:radial-gradient(circle at 35% 35%,#f4f1ec 0 8%,#74736f 9% 42%,#171717 43%); }}
      .audio .orb {{ background:repeating-radial-gradient(circle,#171717 0 3px,#e4e0da 4px 8px); }}
      .depth-node {{ z-index:0; animation:none; pointer-events:none; }}
      .depth-node .orb {{ margin:0 auto; border-color:#777168; background:#777168; box-shadow:none; }}
      .latent-known {{ width:16.1%; opacity:.34; }}
      .latent-known .orb {{ width:72.97%; }}
      .latent-known strong {{ margin-top:7px; font-size:10px; }}
      .latent-private {{ width:6.96%; opacity:.18; }}
      .latent-private .orb {{ width:90.63%; }}
      .unknown {{ width:3.26%; opacity:.10; }}
      .unknown .orb {{ width:86.67%; }}
      .unknown:nth-of-type(even) .orb {{ width:60%; }}
      .stats {{ position:absolute; z-index:5; right:130px; bottom:12px; width:235px; padding-top:8px; border-top:1px solid #111; color:#111; text-decoration:none; font-size:8px; letter-spacing:.09em; line-height:1.55; text-transform:uppercase; }}
      .stats h2 {{ margin:0 0 5px; font-size:12px; letter-spacing:.14em; }}
      .stats div {{ display:grid; grid-template-columns:1fr 1fr; gap:0 .7rem; }}
      .stats b {{ font-weight:500; }}
      .stats small {{ display:block; margin-top:6px; color:#777168; font-size:7px; letter-spacing:.05em; }}
      .stats:hover h2,.stats:focus h2 {{ color:#315f78; }}
      @keyframes wobble {{ from {{ transform:translate(-50%,-50%) rotate(-1.2deg) translateY(-3px); }} to {{ transform:translate(-50%,-50%) rotate(1.2deg) translateY(4px); }} }}
      @media (prefers-reduced-motion:reduce) {{ .node {{ animation:none; }} }}
    </style>
    <div class="field" data-registry='{html.escape(payload)}'>
      {''.join(lines)}
      <a class="hub" href="?view=network&amp;door=access" aria-label="{html.escape(start_label)}">+</a><div class="hub-label">{html.escape(start_label)}</div>
      {''.join(nodes)}
      <a class="stats" href="?view=network&amp;state=art" aria-label="Inspect {html.escape(state_label)}">
        <h2>{html.escape(state_label)} ↗</h2><div>
          <span><b>{state_counts['active']}</b> {html.escape(active_label)}</span>
          <span><b>{state_counts['latent_known']}</b> {html.escape(latent_known_label)}</span>
          <span><b>{state_counts['latent_private']}</b> {html.escape(latent_private_label)}</span>
          <span><b>{state_counts['unknown']}</b> {html.escape(unknown_label)}</span>
          <span><b>{connection_count}</b> {html.escape(connections_label)}</span>
          <span><b>{ratio}</b> {html.escape(ratio_label)}</span>
          <span><b>{active_relation_count}</b> {html.escape(relations_label)}</span>
        </div><small>{html.escape(forthcoming_label)}</small>
      </a>
    </div>
    """
