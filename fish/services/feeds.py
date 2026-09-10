from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from fish.models import Feed, Object

from .ranking import score_object


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:90] or "feed"


def serialize_object(obj: Object, score: float, reasons: list[str]) -> dict[str, Any]:
    metadata = obj.metadata_json or {}
    return {
        "id": obj.id,
        "object_key": obj.object_key,
        "kind": obj.kind,
        "version": obj.version,
        "domain": obj.domain,
        "title": obj.title,
        "summary": obj.summary,
        "confidence": obj.confidence,
        "score": score,
        "reasons": reasons,
        "tags": metadata.get("tags", []),
        "metadata": metadata,
        "created_at": obj.created_at.isoformat(),
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
    }


def get_ranked_feed(session: Session, feed: Feed, limit: int = 50) -> list[dict[str, Any]]:
    rows = session.scalars(
        select(Object)
        .order_by(Object.created_at.desc())
        .limit(1000)
    ).all()
    scored: list[dict[str, Any]] = []
    for obj in rows:
        score, reasons = score_object(obj, feed)
        if score <= 0:
            continue
        scored.append(serialize_object(obj, score, reasons))
    scored.sort(key=lambda x: (x["score"], x["created_at"]), reverse=True)
    return scored[:limit]


def get_delta_feed(session: Session, feed: Feed, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Delta feed: only objects that have changed since user last saw them.
    This is the visionidea2 core primitive."""
    from fish.models import Interaction

    # Get user's last-seen versions
    last_seen: dict[int, int] = {}
    interactions = session.scalars(
        select(Interaction).where(
            Interaction.user_id == user_id,
            Interaction.feed_id == feed.id,
            Interaction.action.in_(["seen", "DONE"]),
        )
    ).all()
    for interaction in interactions:
        last_seen[interaction.object_id] = max(
            last_seen.get(interaction.object_id, 0),
            interaction.object_version,
        )

    # Get all objects, score them
    rows = session.scalars(
        select(Object).order_by(Object.updated_at.desc()).limit(2000)
    ).all()

    scored: list[dict[str, Any]] = []
    for obj in rows:
        score, reasons = score_object(obj, feed)
        if score <= 0:
            continue

        # Delta: if user has seen this version, suppress unless confidence changed materially
        if obj.id in last_seen:
            seen_version = last_seen[obj.id]
            if obj.version <= seen_version:
                # User already saw this version — check if confidence changed materially
                prev_interactions = [
                    i for i in interactions
                    if i.object_id == obj.id and i.object_version == seen_version
                ]
                if prev_interactions:
                    continue  # Skip — no material change

        entry = serialize_object(obj, score, reasons)

        # Add delta context
        if obj.id in last_seen:
            entry["delta"] = f"Updated since you last saw version {last_seen[obj.id]}"
            reasons.append("updated")

        scored.append(entry)

    scored.sort(key=lambda x: (x["score"], x["created_at"]), reverse=True)
    return scored[:limit]


def feed_to_dict(session: Session, feed: Feed, limit: int = 50) -> dict[str, Any]:
    return {
        "feed": {
            "slug": feed.slug,
            "name": feed.name,
            "description": feed.description,
            "prompt": feed.prompt,
            "icon": feed.icon,
            "version": feed.version,
            "weights": feed.weights,
            "filters": feed.filters,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": get_ranked_feed(session, feed, limit),
    }


def feed_to_rss(session: Session, feed: Feed, base_url: str, limit: int = 50) -> str:
    data = get_ranked_feed(session, feed, limit)
    items = []
    for item in data:
        link = f"{base_url}/f/{feed.slug}"
        desc = html.escape(f"{item['summary']}\nScore: {item['score']:.2f}")
        items.append(
            f"<item><title>{html.escape(item['title'])}</title><link>{html.escape(link)}</link>"
            f"<guid isPermaLink=\"false\">feedify:{item['id']}</guid><description>{desc}</description>"
            f"<pubDate>{html.escape(item['created_at'])}</pubDate></item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<rss version=\"2.0\"><channel><title>{html.escape(feed.name)}</title>"
        f"<link>{base_url}/f/{feed.slug}</link><description>{html.escape(feed.description or feed.prompt)}</description>"
        + "".join(items)
        + "</channel></rss>"
    )


def icon_png(feed: Feed, size: int = 512) -> bytes:
    digest = sha256(feed.slug.encode()).digest()
    bg = tuple(40 + (x % 170) for x in digest[:3])
    image = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(image)
    text = (feed.icon or "⚡")[:2]
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size * 0.5))
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (size - (bbox[2] - bbox[0])) / 2
    y = (size - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), text, fill="white", font=font)
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def manifest(feed: Feed, base_url: str) -> dict[str, Any]:
    return {
        "name": feed.name,
        "short_name": feed.name[:12],
        "start_url": f"/f/{feed.slug}?installed=1",
        "display": "standalone",
        "background_color": "#0b0c10",
        "theme_color": "#0b0c10",
        "icons": [
            {"src": f"{base_url}/icon/{feed.slug}/192.png", "sizes": "192x192", "type": "image/png"},
            {"src": f"{base_url}/icon/{feed.slug}/512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
