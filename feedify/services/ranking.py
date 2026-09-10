from __future__ import annotations

import re
from datetime import datetime, timezone
from math import exp
from typing import Any

from feedify.models import Feed, Object

STOPWORDS = {
    "and", "are", "but", "can", "concrete", "from", "into", "new", "not", "only",
    "show", "that", "the", "their", "them", "this", "things", "want", "what", "when",
    "where", "which", "with", "you", "your",
}

DEFAULT_WEIGHTS = {
    "confidence": 1.0,
    "novelty": 1.15,
    "actionability": 1.0,
    "freshness": 1.0,
}


def _words(text: str) -> set[str]:
    return {
        w
        for w in re.findall(r"[a-z0-9][a-z0-9+._-]{2,}", text.lower())
        if len(w) >= 3 and w not in STOPWORDS
    }


def score_object(obj: Object, feed: Feed) -> tuple[float, list[str]]:
    weights = {**DEFAULT_WEIGHTS, **(feed.weights or {})}
    filters = feed.filters or {}
    now = datetime.now(timezone.utc)
    created = obj.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_hours = max((now - created).total_seconds() / 3600, 0)
    freshness = exp(-age_hours / (24 * float(filters.get("half_life_days", 10))))

    metadata = obj.metadata_json or {}
    confidence = obj.confidence or 0.5

    numerator = (
        confidence * weights["confidence"]
        + freshness * weights["freshness"]
        + metadata.get("novelty", 0.5) * weights.get("novelty", 1.0)
        + metadata.get("actionability", 0.5) * weights.get("actionability", 1.0)
    )
    denominator = sum(max(v, 0) for v in weights.values()) or 1
    score = numerator / denominator
    reasons: list[str] = []

    allowed_domains = set(filters.get("domains") or [])
    if allowed_domains and obj.domain not in allowed_domains:
        return 0.0, ["domain-filtered"]

    allowed_kinds = set(filters.get("kinds") or [])
    if allowed_kinds and obj.kind not in allowed_kinds:
        return 0.0, ["kind-filtered"]

    haystack = " ".join([obj.title, obj.summary, " ".join(metadata.get("tags", []))]).lower()
    include = set(filters.get("include_keywords") or []) | _words(feed.prompt or "")
    exclude = set(filters.get("exclude_keywords") or [])

    matched = [kw for kw in include if kw.lower() in haystack]
    blocked = [kw for kw in exclude if kw.lower() in haystack]
    if blocked:
        score *= 0.12
        reasons.append(f"excluded:{','.join(blocked[:3])}")
    if matched:
        boost = min(0.22, 0.035 * len(matched))
        score += boost
        reasons.append(f"matched:{','.join(matched[:4])}")

    if confidence >= 0.82:
        reasons.append("high-confidence")
    if metadata.get("viral"):
        reasons.append("viral")
    if metadata.get("insider_score", 0) >= 70:
        reasons.append("high-insider-score")

    min_score = float(filters.get("min_score", 0.0))
    if score < min_score:
        return 0.0, ["below-threshold"]
    return round(min(max(score, 0.0), 1.0), 4), reasons


def infer_algorithm_from_prompt(prompt: str) -> tuple[dict[str, float], dict[str, Any]]:
    text = prompt.lower()
    weights = dict(DEFAULT_WEIGHTS)
    domains = []
    mapping = {
        "ios": "ios",
        "app store": "ios",
        "shopify": "commerce",
        "commerce": "commerce",
        "ecom": "commerce",
        "seo": "seo",
        "search": "seo",
        "agent": "agents",
        "mcp": "agents",
        "meta": "distribution",
        "ads": "distribution",
        "quantum": "quantum",
        "insider": "insiders",
        "sec": "insiders",
    }
    for needle, domain in mapping.items():
        if needle in text and domain not in domains:
            domains.append(domain)
    if "alpha" in text or "novel" in text or "new" in text:
        weights["novelty"] = 1.35
    if "build" in text or "ship" in text or "opportunity" in text:
        weights["actionability"] = 1.45
    if "less noise" in text or "high signal" in text or "only" in text:
        min_score = 0.69
    else:
        min_score = 0.55
    filters: dict[str, Any] = {
        "min_score": min_score,
        "half_life_days": 9,
        "include_keywords": sorted(_words(prompt))[:24],
        "exclude_keywords": ["giveaway", "politics", "meme"],
    }
    if domains:
        filters["domains"] = domains
    return weights, filters
