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

from feedify.models import Feed, Signal

from .ranking import score_signal


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:90] or "feed"


def serialize_signal(signal: Signal, score: float, reasons: list[str]) -> dict[str, Any]:
    record = signal.record
    return {
        "id": signal.id,
        "type": signal.signal_type,
        "domain": signal.domain,
        "title": signal.title,
        "summary": signal.summary,
        "why_it_matters": signal.why_it_matters,
        "score": score,
        "reasons": reasons,
        "tags": signal.tags or [],
        "metrics": record.metrics if record else {},
        "source": {
            "type": record.source_type if record else None,
            "author": record.author if record else None,
            "url": record.url if record else None,
            "published_at": record.published_at.isoformat() if record and record.published_at else None,
        },
        "created_at": signal.created_at.isoformat(),
    }


def get_ranked_feed(session: Session, feed: Feed, limit: int = 50) -> list[dict[str, Any]]:
    rows = session.scalars(
        select(Signal)
        .options(joinedload(Signal.record))
        .order_by(Signal.created_at.desc())
        .limit(1000)
    ).all()
    scored: list[dict[str, Any]] = []
    for signal in rows:
        score, reasons = score_signal(signal, feed)
        if score <= 0:
            continue
        scored.append(serialize_signal(signal, score, reasons))
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
        link = item["source"].get("url") or f"{base_url}/f/{feed.slug}"
        desc = html.escape(f"{item['summary']}\n\nWhy it matters: {item['why_it_matters']}\nScore: {item['score']:.2f}")
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
