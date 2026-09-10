"""Recursive expansion service for Feedify 2.0.

When a high-scoring post appears, recursively crawl:
1. Who they replied to
2. Who replied intelligently
3. Paper coauthors
4. GitHub contributors

This is how we discover the 43-follower accounts that the aithesis document describes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from fish.settings import get_settings
from fish.services.detector import get_source_distance, get_source_proximity, compute_expected_alpha


async def discover_accounts_from_post(
    author_handle: str,
    reply_to_handle: str | None = None,
    reply_to_user: str | None = None,
    text: str = "",
    max_depth: int = 1,
    depth: int = 0,
) -> list[dict[str, Any]]:
    """Discover new high-signal accounts from a post's context.
    
    Returns list of account dicts to potentially add to watchlist.
    """
    if depth >= max_depth:
        return []

    discovered = []
    settings = get_settings()

    # The reply_to user is potentially high-signal (someone worth replying to)
    if reply_to_user and reply_to_user != author_handle:
        existing_distance = get_source_distance(reply_to_user)
        if existing_distance >= 3:  # Not already in watchlist as experimenter
            discovered.append({
                "handle": reply_to_user,
                "source": "reply_context",
                "reason": f"@{author_handle} replied to them",
                "suggested_distance": max(0, existing_distance - 1),
            })

    # TODO: When LLM is available, use it to extract mentioned accounts
    # and assess whether they're high-signal based on the context.

    return discovered


async def expand_watchlist_from_graph(
    session,
    min_alpha: float = 0.5,
    max_new_accounts: int = 20,
) -> list[dict[str, Any]]:
    """Scan recent high-alpha objects and discover new accounts to watch.
    
    Returns list of accounts that should be added to the watchlist.
    """
    from fish.models import Object, Edge, Artifact
    from sqlalchemy import select

    # Find high-alpha objects from the last 7 days
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    high_alpha_objects = session.scalars(
        select(Object).where(
            Object.created_at >= cutoff,
            Object.confidence >= 0.6,
        ).order_by(Object.confidence.desc()).limit(50)
    ).all()

    candidates = []
    seen_handles = set()

    for obj in high_alpha_objects:
        meta = obj.metadata_json or {}
        author_handle = meta.get("author_handle")
        if not author_handle:
            continue

        # Check if this person is already well-tracked
        existing_distance = get_source_distance(author_handle)
        if existing_distance <= 1:
            continue  # Already tracked as experimenter/collaborator

        if author_handle in seen_handles:
            continue
        seen_handles.add(author_handle)

        # This person produced a high-alpha post but isn't in our watchlist
        # They should be added with a suggested source_distance
        candidates.append({
            "handle": author_handle,
            "source": "high_alpha_discovery",
            "reason": f"Produced high-alpha object: {obj.title[:80]}",
            "suggested_distance": 0,  # They're running experiments
            "alpha_score": obj.confidence,
            "domain": obj.domain,
            "kind": obj.kind,
        })

    # Sort by alpha score and limit
    candidates.sort(key=lambda x: x.get("alpha_score", 0), reverse=True)
    return candidates[:max_new_accounts]


def add_to_watchlist(
    handle: str,
    source_distance: int = 0,
    domain: str = "general",
    lab: str = "",
    role: str = "",
    priority: str = "A",
    reason: str = "",
) -> bool:
    """Add a new account to the acceleration watchlist.
    Returns True if added, False if already exists."""
    watchlist_path = Path(__file__).parent.parent.parent / "config" / "acceleration_watchlist.json"

    try:
        entries = json.loads(watchlist_path.read_text())
    except (OSError, json.JSONDecodeError):
        entries = []

    # Check if already exists
    existing_handles = {e.get("handle", "").lower() for e in entries}
    if handle.lower() in existing_handles:
        return False

    entries.append({
        "handle": handle,
        "source_distance": source_distance,
        "domain": domain,
        "lab": lab,
        "role": role,
        "priority": priority,
        "discovered_by": "recursive_expansion",
        "discovery_reason": reason,
    })

    watchlist_path.write_text(json.dumps(entries, indent=2))
    return True
