from __future__ import annotations

from datetime import datetime, timezone
from math import log10
from typing import Iterable

from feedify.schemas import NormalizedItem, SignalDraft


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _text(item: NormalizedItem) -> str:
    return f"{item.title} {item.body or ''} {' '.join(map(str, item.metrics.get('topics', [])))}".lower()


def infer_domain(item: NormalizedItem) -> str:
    text = _text(item)
    if any(k in text for k in ("shopify", "commerce", "marketplace", "retail", "checkout", "ecommerce")):
        return "commerce"
    if any(k in text for k in ("ios", "iphone", "app store", "mobile app", "revenuecat")):
        return "ios"
    if any(k in text for k in ("seo", "search", "crawl", "indexnow", "serp")):
        return "seo"
    if any(k in text for k in ("mcp", "agent", "tool", "api", "sdk", "protocol")):
        return "agents"
    if any(k in text for k in ("ads", "meta", "tiktok", "creative", "acquisition")):
        return "distribution"
    return "general"


def detect(item: NormalizedItem) -> list[SignalDraft]:
    fn = globals().get(f"detect_{item.source_type}")
    if callable(fn):
        signals = fn(item)
        if signals:
            return signals
    return detect_generic(item)


def detect_trustmrr(item: NormalizedItem) -> list[SignalDraft]:
    m = item.metrics
    revenue = float(m.get("last30d_revenue_cents") or 0) / 100
    growth_raw = m.get("growth30d")
    growth = float(growth_raw or 0)
    # TrustMRR has historically represented this field as either a decimal or a percentage;
    # normalize defensively.
    growth_pct = growth * 100 if abs(growth) <= 2 else growth
    multiple = m.get("multiple")
    domain = "ios" if m.get("category") == "mobile-apps" else "commerce" if m.get("category") == "ecommerce" else "startups"
    signals: list[SignalDraft] = []
    if revenue >= 1_000 and growth_pct >= 10:
        score = clamp(0.55 + min(growth_pct, 200) / 500 + min(log10(max(revenue, 1)), 6) / 20)
        signals.append(
            SignalDraft(
                signal_type="REVENUE_ACCELERATION",
                domain=domain,
                title=f"{item.title} is accelerating on verified revenue",
                summary=f"Verified last-30-day revenue is about ${revenue:,.0f}; reported 30-day growth is {growth_pct:.1f}%.",
                why_it_matters="Economic validation is already present; inspect acquisition, product simplicity, founder footprint and replication wedges.",
                novelty=0.72,
                actionability=0.88,
                source_proximity=0.96,
                confidence=0.9,
                evidence_strength=0.96,
                tags=["verified-revenue", "breakout", m.get("category") or "startup"],
                metadata={"suggested_score": score},
            )
        )
    if m.get("on_sale") and multiple is not None and float(multiple) <= 2.5:
        signals.append(
            SignalDraft(
                signal_type="ACQUISITION_MISPRICING",
                domain="startups",
                title=f"{item.title} is listed at a low revenue multiple",
                summary=f"Asking multiple is {float(multiple):.2f}x with roughly ${revenue:,.0f} last-30-day revenue.",
                why_it_matters="Even if you do not buy it, the listing can reveal a validated niche, traffic source, stack and pricing model.",
                novelty=0.76,
                actionability=0.8,
                source_proximity=0.95,
                confidence=0.86,
                evidence_strength=0.9,
                tags=["acquisition", "validated-niche"],
            )
        )
    if not signals:
        signals.append(
            SignalDraft(
                signal_type="VERIFIED_BUSINESS",
                domain=domain,
                title=f"Verified business: {item.title}",
                summary=f"TrustMRR reports approximately ${revenue:,.0f} in last-30-day revenue.",
                why_it_matters="Use as a market-validation input rather than founder commentary.",
                novelty=0.45,
                actionability=0.58,
                source_proximity=0.96,
                confidence=0.9,
                evidence_strength=0.95,
                tags=[m.get("category") or "startup"],
            )
        )
    return signals


def detect_glama(item: NormalizedItem) -> list[SignalDraft]:
    m = item.metrics
    cats = [str(x) for x in (m.get("categories") or [])]
    text = _text(item)
    commerce = any(x in text for x in ("commerce", "retail", "shop", "marketplace", "payment"))
    return [
        SignalDraft(
            signal_type="NEW_CAPABILITY",
            domain="commerce" if commerce else "agents",
            title=f"New MCP capability: {item.title}",
            summary=item.body or f"A discoverable MCP server from {item.author or 'an independent builder'}.",
            why_it_matters="Ask what workflow becomes newly automatable when this tool is combined with payments, search, identity or marketplace adapters.",
            novelty=0.88,
            actionability=0.82,
            source_proximity=0.9 if m.get("official") else 0.72,
            confidence=0.78,
            evidence_strength=0.8,
            tags=["mcp", "primitive", *cats[:4]],
        )
    ]


def detect_github(item: NormalizedItem) -> list[SignalDraft]:
    stars = int(item.metrics.get("stars") or 0)
    topics = item.metrics.get("topics") or []
    text = _text(item)
    primitive = any(k in text for k in ("mcp", "sdk", "api", "agent", "browser", "commerce", "scrap", "payment", "search"))
    novelty = clamp(0.55 + min(stars, 2500) / 5000 + (0.12 if primitive else 0))
    return [
        SignalDraft(
            signal_type="REPO_ACCELERATION",
            domain=infer_domain(item),
            title=f"Fast new repo: {item.title}",
            summary=f"Created recently and already at {stars:,} stars. {item.body or ''}".strip(),
            why_it_matters="Rapid adoption can indicate a newly usable technical primitive before product-layer commentary catches up.",
            novelty=novelty,
            actionability=0.8 if primitive else 0.58,
            source_proximity=0.84,
            confidence=0.78,
            evidence_strength=0.8,
            tags=["github", "open-source", *topics[:5]],
        )
    ]


def detect_hackernews(item: NormalizedItem) -> list[SignalDraft]:
    score = int(item.metrics.get("score") or 0)
    return [
        SignalDraft(
            signal_type="EARLY_BUILDER_SIGNAL",
            domain=infer_domain(item),
            title=item.title.replace("Show HN:", "Early launch:").strip(),
            summary=item.body or "Early builder launch surfaced on Hacker News.",
            why_it_matters="Useful as an early discovery layer; require corroboration from usage, GitHub acceleration or economic data before acting.",
            novelty=0.78,
            actionability=0.68,
            source_proximity=0.78,
            confidence=0.62,
            evidence_strength=clamp(0.4 + score / 400),
            tags=["show-hn", "early"],
        )
    ]


def detect_storeleads(item: NormalizedItem) -> list[SignalDraft]:
    m = item.metrics
    delta = int(m.get("installs_30d") or 0)
    installs = int(m.get("installs") or 0)
    created = item.published_at
    days = (datetime.now(timezone.utc) - created).days if created else 9999
    strength = clamp(0.5 + max(delta, 0) / 200 + (0.12 if days < 180 else 0))
    return [
        SignalDraft(
            signal_type="TECH_ADOPTION",
            domain="commerce",
            title=f"Shopify app signal: {item.title}",
            summary=f"Store Leads reports {installs:,} installs and {delta:+,} net installs over 30 days.",
            why_it_matters="App adoption reveals where merchants are spending money and where new platform wedges may be emerging.",
            novelty=0.72 if days < 365 else 0.52,
            actionability=0.86,
            source_proximity=0.94,
            confidence=0.88,
            evidence_strength=strength,
            tags=["shopify", "app-adoption", *(m.get("categories") or [])[:4]],
        )
    ]


def detect_appfigures(item: NormalizedItem) -> list[SignalDraft]:
    revenue = float(item.metrics.get("revenue_30d") or 0)
    downloads = int(item.metrics.get("downloads_30d") or 0)
    return [
        SignalDraft(
            signal_type="APP_BREAKOUT",
            domain="ios",
            title=f"App economics: {item.title}",
            summary=f"Appfigures estimates {downloads:,} downloads and ${revenue:,.0f} revenue over the configured 30-day window.",
            why_it_matters="Use app-level economic evidence to rank cloning, verticalization, localization and distribution opportunities.",
            novelty=0.7,
            actionability=0.9,
            source_proximity=0.94,
            confidence=0.82,
            evidence_strength=0.9,
            tags=["app-store", "revenue-estimate"],
        )
    ]


def detect_rss(item: NormalizedItem) -> list[SignalDraft]:
    return [
        SignalDraft(
            signal_type="PLATFORM_CHANGE",
            domain=infer_domain(item),
            title=item.title,
            summary=(item.body or "")[:700],
            why_it_matters="Primary-source changelogs and engineering feeds often expose platform changes before secondary commentary.",
            novelty=0.7,
            actionability=0.7,
            source_proximity=0.86,
            confidence=0.82,
            evidence_strength=0.82,
            tags=["rss", "primary-source"],
        )
    ]


def detect_generic(item: NormalizedItem) -> list[SignalDraft]:
    return [
        SignalDraft(
            signal_type="OBSERVATION",
            domain=infer_domain(item),
            title=item.title,
            summary=(item.body or "")[:700],
            why_it_matters="Potentially relevant source item; lower confidence until corroborated.",
            novelty=0.5,
            actionability=0.5,
            source_proximity=0.55,
            confidence=0.5,
            evidence_strength=0.5,
            tags=[item.source_type],
        )
    ]


def calculate_base_score(draft: SignalDraft) -> float:
    return round(
        clamp(
            0.27 * draft.novelty
            + 0.28 * draft.actionability
            + 0.18 * draft.source_proximity
            + 0.14 * draft.evidence_strength
            + 0.13 * draft.confidence
        ),
        4,
    )


def detect_many(items: Iterable[NormalizedItem]) -> list[tuple[NormalizedItem, SignalDraft]]:
    return [(item, signal) for item in items for signal in detect(item)]
