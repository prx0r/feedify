from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from fish.db import SessionLocal, init_db
from fish.models import Feed, Object, Artifact
from fish.services.ranking import infer_algorithm_from_prompt


FEEDS = [
    (
        "quantum-scarcity",
        "Quantum Scarcity",
        "⚛",
        "Physical-scarcity shocks from quantum breakthroughs: fabrication, cryogenic wafer test, qubit control, cryogenics, photonics, trapped-ion and superconducting progress, and post-quantum migration urgency. Map each claim to implied tickers and surface whatever hasn't repriced yet.",
    ),
    (
        "things-to-build",
        "Things I Should Build",
        "⚡",
        "Only show me newly buildable opportunities I can ship quickly, with strong evidence, high novelty and low noise.",
    ),
    (
        "agent-commerce-alpha",
        "Agent Commerce Alpha",
        "◈",
        "New MCPs, APIs, payment primitives, marketplaces, merchant infrastructure and protocol changes that unlock a concrete agentic-commerce product.",
    ),
    (
        "ios-gold",
        "iOS Gold",
        "A",
        "High-signal iOS app opportunities: revenue breakouts, App Store distribution tactics, subscription economics and unusually simple apps with proven demand.",
    ),
    (
        "hidden-experts",
        "Hidden Experts",
        "◎",
        "Primary-source engineers, PMs and protocol authors. Prefer insider disclosures, obscure technical replies, source proximity and details not repeated by generic AI accounts.",
    ),
    (
        "seo-distribution",
        "SEO + Distribution",
        "↗",
        "Concrete SEO, Google/Bing crawling, Meta ads, app acquisition and distribution platform changes. Suppress generic growth advice.",
    ),
]


DEMO_OBJECTS = [
    {
        "key": "pick:marketplace_mcp",
        "kind": "pick",
        "title": "Marketplace MCP exposes fragmented resale inventory",
        "summary": "A new MCP makes fragmented marketplace inventory queryable by agents.",
        "domain": "commerce",
        "confidence": 0.82,
        "tags": ["mcp", "marketplace", "resale", "demo"],
    },
    {
        "key": "pick:solo_breakout",
        "kind": "pick",
        "title": "Tiny utility crossed meaningful verified MRR",
        "summary": "A small mobile utility shows verified revenue growth despite a minimal product surface.",
        "domain": "ios",
        "confidence": 0.91,
        "tags": ["verified-revenue", "mobile-apps", "demo"],
    },
    {
        "key": "technology:browser_agent",
        "kind": "technology",
        "title": "New browser-agent repo is accelerating",
        "summary": "A newly created browser automation repository is rapidly gaining developer adoption.",
        "domain": "agents",
        "confidence": 0.78,
        "tags": ["github", "browser", "agent", "demo"],
    },
    {
        "key": "entity:shopify_app",
        "kind": "entity",
        "title": "Shopify merchant tooling shows rapid adoption",
        "summary": "A narrowly scoped Shopify app is adding installations quickly across active merchants.",
        "domain": "commerce",
        "confidence": 0.88,
        "tags": ["shopify", "adoption", "demo"],
    },
    {
        "key": "claim:platform_change",
        "kind": "claim",
        "title": "Search platform changes how sites expose actions to agents",
        "summary": "A search/web platform change makes structured site actions more directly consumable by agents.",
        "domain": "seo",
        "confidence": 0.85,
        "tags": ["seo", "webmcp", "primary-source", "demo"],
    },
]


def seed() -> None:
    init_db()
    with SessionLocal() as session:
        for slug, name, icon, prompt in FEEDS:
            existing = session.scalar(select(Feed).where(Feed.slug == slug))
            if existing:
                continue
            weights, filters = infer_algorithm_from_prompt(prompt)
            session.add(
                Feed(
                    slug=slug,
                    name=name,
                    icon=icon,
                    prompt=prompt,
                    description=prompt,
                    public=True,
                    weights=weights,
                    filters=filters,
                )
            )
        if session.scalar(select(Object).limit(1)) is None:
            now = datetime.now(timezone.utc)
            for idx, row in enumerate(DEMO_OBJECTS):
                session.add(
                    Object(
                        object_key=row["key"],
                        kind=row["kind"],
                        title=row["title"],
                        summary=row["summary"],
                        domain=row["domain"],
                        confidence=row["confidence"],
                        metadata_json={"tags": row["tags"], "demo": True},
                        created_at=now - timedelta(hours=idx * 3),
                        updated_at=now - timedelta(hours=idx * 3),
                    )
                )
        session.commit()
