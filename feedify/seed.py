from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from feedify.db import SessionLocal, init_db
from feedify.models import Feed, Signal, SourceRecord
from feedify.services.ranking import infer_algorithm_from_prompt


FEEDS = [
    (
        "things-to-build",
        "Things I Should Build",
        "⚡",
        "Only show me newly buildable opportunities I can ship quickly, with strong evidence, high novelty and low noise across iOS, agentic commerce, SEO, distribution and developer primitives.",
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


DEMO_SIGNALS = [
    {
        "source": "glama",
        "external": "demo/marketplace-mcp",
        "title": "Marketplace MCP exposes fragmented resale inventory",
        "url": "https://glama.ai/mcp/servers",
        "body": "Demo seed representing a newly discoverable marketplace MCP primitive.",
        "type": "NEW_CAPABILITY",
        "domain": "commerce",
        "summary": "A new MCP makes fragmented marketplace inventory queryable by agents.",
        "why": "Combine search, sold comps, logistics and payments into automated sourcing/resale workflows.",
        "scores": (0.94, 0.95, 0.82, 0.82, 0.8),
        "tags": ["mcp", "marketplace", "resale", "demo"],
    },
    {
        "source": "trustmrr",
        "external": "demo/solo-breakout",
        "title": "Tiny utility crossed meaningful verified MRR",
        "url": "https://trustmrr.com/",
        "body": "Demo seed representing a low-complexity, verified-revenue startup breakout.",
        "type": "REVENUE_ACCELERATION",
        "domain": "ios",
        "summary": "A small mobile utility shows verified revenue growth despite a minimal product surface.",
        "why": "Inspect acquisition, pricing and reviews to identify a vertical or localized replication wedge.",
        "scores": (0.86, 0.94, 0.97, 0.91, 0.96),
        "tags": ["verified-revenue", "mobile-apps", "demo"],
    },
    {
        "source": "github",
        "external": "demo/browser-agent",
        "title": "New browser-agent repo is accelerating",
        "url": "https://github.com/trending",
        "body": "Demo seed representing a fast-growing new technical primitive.",
        "type": "REPO_ACCELERATION",
        "domain": "agents",
        "summary": "A newly created browser automation repository is rapidly gaining developer adoption.",
        "why": "The primitive can collapse the cost of building vertical agents that previously required bespoke browser-driving infrastructure.",
        "scores": (0.91, 0.86, 0.83, 0.78, 0.79),
        "tags": ["github", "browser", "agent", "demo"],
    },
    {
        "source": "storeleads",
        "external": "demo/shopify-app",
        "title": "Shopify merchant tooling shows rapid adoption",
        "url": "https://storeleads.app/",
        "body": "Demo seed representing a Store Leads app adoption signal.",
        "type": "TECH_ADOPTION",
        "domain": "commerce",
        "summary": "A narrowly scoped Shopify app is adding installations quickly across active merchants.",
        "why": "Rapid merchant adoption reveals a willingness to pay and an emerging workflow worth competing on or integrating into.",
        "scores": (0.72, 0.9, 0.95, 0.88, 0.91),
        "tags": ["shopify", "adoption", "demo"],
    },
    {
        "source": "rss",
        "external": "demo/search-engineering",
        "title": "Search platform changes how sites expose actions to agents",
        "url": "https://www.w3.org/",
        "body": "Demo seed representing a primary-source platform or standards change.",
        "type": "PLATFORM_CHANGE",
        "domain": "seo",
        "summary": "A search/web platform change makes structured site actions more directly consumable by agents.",
        "why": "Sites that compile their data/actions early can gain an agent-discovery advantage before the practice becomes standard SEO advice.",
        "scores": (0.88, 0.84, 0.96, 0.85, 0.86),
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
        if session.scalar(select(Signal).limit(1)) is None:
            now = datetime.now(timezone.utc)
            for idx, row in enumerate(DEMO_SIGNALS):
                rec = SourceRecord(
                    source_type=row["source"],
                    external_id=row["external"],
                    title=row["title"],
                    url=row["url"],
                    body=row["body"],
                    observed_at=now - timedelta(hours=idx * 3),
                    published_at=now - timedelta(days=idx + 1),
                    metrics={"demo": True},
                    raw={"demo": True},
                )
                session.add(rec)
                session.flush()
                novelty, actionability, proximity, confidence, evidence = row["scores"]
                base = round(0.27 * novelty + 0.28 * actionability + 0.18 * proximity + 0.14 * evidence + 0.13 * confidence, 4)
                session.add(
                    Signal(
                        record_id=rec.id,
                        signal_type=row["type"],
                        domain=row["domain"],
                        title=row["title"],
                        summary=row["summary"],
                        why_it_matters=row["why"],
                        novelty=novelty,
                        actionability=actionability,
                        source_proximity=proximity,
                        confidence=confidence,
                        evidence_strength=evidence,
                        base_score=base,
                        tags=row["tags"],
                        metadata_json={"demo": True},
                        created_at=now - timedelta(hours=idx * 3),
                    )
                )
        session.commit()
