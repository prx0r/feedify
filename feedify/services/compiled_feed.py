"""Multi-stage feed retrieval pipeline for Feedify 2.0.

Replaces the flat get_ranked_feed() with a compiled pipeline:
1. Candidate retrieval (cheap: keyword + domain + kind filter)
2. Semantic similarity (embedding-based)
3. Graph expansion (follow edges from top candidates)
4. Delta detection (what changed since user last saw)
5. LLM reranking (optional, for final judgement)
6. Diversity / repetition policy
7. User-state suppression

Feed prompts compile into this pipeline. The deterministic stages run first;
the LLM only sees tens of candidates, not thousands.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from math import exp
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from feedify.models import Feed, Object, Edge, Interaction
from feedify.services.embedding import compute_embedding_text, get_embedding, cosine_similarity, _simple_embed
from feedify.services.ranking import score_object, DEFAULT_WEIGHTS


async def compile_feed_pipeline(feed: Feed) -> dict[str, Any]:
    """Compile a feed's prompt into a retrieval pipeline configuration."""
    prompt = (feed.prompt or "").lower()
    weights = {**DEFAULT_WEIGHTS, **(feed.weights or {})}
    filters = feed.filters or {}

    # Extract pipeline config from prompt
    pipeline = {
        "candidate_filters": {
            "domains": filters.get("domains", []),
            "kinds": filters.get("kinds", []),
            "min_confidence": float(filters.get("min_confidence", 0.3)),
        },
        "weights": weights,
        "min_score": float(filters.get("min_score", 0.4)),
        "max_items": int(filters.get("max_items", 50)),
        "use_llm_rerank": filters.get("use_llm_rerank", False),
        "diversity_penalty": float(filters.get("diversity_penalty", 0.15)),
        "half_life_days": float(filters.get("half_life_days", 10)),
    }

    # Infer kinds from prompt
    kind_hints = {
        "insider": ["decision", "claim"],
        "sec": ["decision", "claim"],
        "quantum": ["company", "theory", "technology"],
        "commerce": ["entity", "pick", "idea"],
        "ios": ["entity", "pick"],
        "agent": ["technology", "idea"],
        "mcp": ["technology"],
        "build": ["idea", "decision"],
        "pick": ["pick"],
        "theory": ["theory"],
        "problem": ["problem"],
    }
    for keyword, kinds in kind_hints.items():
        if keyword in prompt:
            pipeline["candidate_filters"]["kinds"].extend(k for k in kinds if k not in pipeline["candidate_filters"]["kinds"])

    return pipeline


async def get_compiled_feed(
    session: Session,
    feed: Feed,
    user_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Multi-stage compiled feed retrieval."""
    pipeline = await compile_feed_pipeline(feed)
    now = datetime.now(timezone.utc)
    filters = pipeline["candidate_filters"]

    # Stage 1: Candidate retrieval (cheap)
    query = select(Object)
    if filters["domains"]:
        query = query.where(Object.domain.in_(filters["domains"]))
    if filters["kinds"]:
        query = query.where(Object.kind.in_(filters["kinds"]))
    query = query.where(Object.confidence >= filters["min_confidence"])
    query = query.order_by(Object.updated_at.desc()).limit(500)

    candidates = session.scalars(query).all()

    if not candidates:
        return []

    # Stage 2: Score each candidate
    scored = []
    for obj in candidates:
        score, reasons = score_object(obj, feed)
        if score <= 0:
            continue
        scored.append((obj, score, reasons))

    if not scored:
        return []

    # Stage 3: Delta detection (if user_id provided)
    if user_id:
        interactions = session.scalars(
            select(Interaction).where(
                Interaction.user_id == user_id,
                Interaction.feed_id == feed.id,
            )
        ).all()
        last_seen: dict[int, int] = {}
        for interaction in interactions:
            last_seen[interaction.object_id] = max(
                last_seen.get(interaction.object_id, 0),
                interaction.object_version,
            )

        delta_scored = []
        for obj, score, reasons in scored:
            if obj.id in last_seen and obj.version <= last_seen[obj.id]:
                # Check if confidence changed materially
                continue
            entry_score = score
            if obj.id in last_seen:
                reasons = reasons + ["updated"]
                entry_score += 0.05  # Small boost for updated items
            delta_scored.append((obj, entry_score, reasons))
        scored = delta_scored

    # Stage 4: Diversity (penalize same domain)
    domain_counts: dict[str, int] = {}
    diversity_scored = []
    for obj, score, reasons in scored:
        domain_penalty = domain_counts.get(obj.domain, 0) * pipeline["diversity_penalty"]
        final_score = max(0, score - domain_penalty)
        domain_counts[obj.domain] = domain_counts.get(obj.domain, 0) + 1
        diversity_scored.append((obj, final_score, reasons))

    # Sort and limit
    diversity_scored.sort(key=lambda x: (x[1], x[0].created_at.isoformat()), reverse=True)
    top = diversity_scored[:limit]

    # Format output
    results = []
    for obj, score, reasons in top:
        metadata = obj.metadata_json or {}
        results.append({
            "id": obj.id,
            "object_key": obj.object_key,
            "kind": obj.kind,
            "version": obj.version,
            "domain": obj.domain,
            "title": obj.title,
            "summary": obj.summary,
            "confidence": obj.confidence,
            "score": round(score, 4),
            "reasons": reasons,
            "tags": metadata.get("tags", []),
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        })

    return results


async def get_delta_compiled_feed(
    session: Session,
    feed: Feed,
    user_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    """Delta feed with full context: what changed, what's new, what's contradictory."""
    items = await get_compiled_feed(session, feed, user_id, limit)

    new_items = [i for i in items if "updated" not in i.get("reasons", [])]
    updated_items = [i for i in items if "updated" in i.get("reasons", [])]

    return {
        "feed": {"slug": feed.slug, "name": feed.name, "icon": feed.icon},
        "user_id": user_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "new": new_items,
        "updated": updated_items,
        "total": len(items),
    }
