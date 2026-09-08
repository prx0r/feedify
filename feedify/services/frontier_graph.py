"""Build the Minimal Graph from X data.

Simple approach:
1. People are entities
2. Labs are entities
3. Topics are entities
4. Connections emerge from co-occurrence in tweets

No fancy schemas. The LLM does the semantic intelligence.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from feedify.models import Signal, SourceRecord
from feedify.services.minimal_graph import Connection, Entity, MinimalGraph


def build_minimal_graph(db: Session, limit: int = 500) -> MinimalGraph:
    """Build the minimal intelligence graph."""
    graph = MinimalGraph()

    # Load watchlist
    watchlist_path = Path(__file__).parent.parent.parent / "config" / "acceleration_watchlist.json"
    account_map = {}
    if watchlist_path.exists():
        for entry in json.loads(watchlist_path.read_text()):
            account_map[entry["handle"].lower()] = entry

    # Get all X signals
    stmt = (
        select(Signal)
        .options(joinedload(Signal.record))
        .join(SourceRecord)
        .where(SourceRecord.source_type == "x")
        .order_by(Signal.created_at.desc())
        .limit(limit)
    )
    rows = db.scalars(stmt).all()

    # Track interactions for hidden person detection
    interactions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for s in rows:
        if not s.record:
            continue

        metrics = s.record.metrics or {}
        author_handle = str(metrics.get("author_handle", s.record.author or ""))
        if not author_handle:
            continue

        # Get account info from watchlist
        info = account_map.get(author_handle.lower(), {})
        lab = info.get("lab", "")
        role = info.get("role", "")
        priority = info.get("priority", "")

        # Add person entity
        person_id = f"person:{author_handle}"
        if person_id not in graph.entities:
            graph.entities[person_id] = Entity(
                id=person_id,
                name=author_handle,
                entity_type="person",
                metadata={
                    "lab": lab,
                    "role": role,
                    "priority": priority,
                    "followers": metrics.get("author_followers", 0),
                },
            )

        # Add lab entity
        if lab:
            lab_id = f"org:{lab}"
            if lab_id not in graph.entities:
                graph.entities[lab_id] = Entity(
                    id=lab_id,
                    name=lab,
                    entity_type="org",
                )
            # Connect person → lab
            graph.add_connection(Connection(
                source=person_id,
                target=lab_id,
                relation="works_at",
                weight=1.0,
                evidence_ids=[s.record.external_id],
            ))

        # Extract topics from text
        text = (s.title or "").lower() + " " + (s.summary or "").lower()
        topics_found = set()
        for topic in ["qec", "rl", "reasoning", "agent", "silicon", "materials",
                      "protein", "robot", "verification", "formal", "photonic",
                      "interconnect", "experiment", "simulation", "compiler"]:
            if topic in text:
                topics_found.add(topic)

        for topic in topics_found:
            topic_id = f"topic:{topic}"
            if topic_id not in graph.entities:
                graph.entities[topic_id] = Entity(
                    id=topic_id,
                    name=topic,
                    entity_type="topic",
                )
            # Connect person → topic
            graph.add_connection(Connection(
                source=person_id,
                target=topic_id,
                relation="works_on",
                weight=0.5,
                evidence_ids=[s.record.external_id],
            ))

        # Track reply interactions for hidden person detection
        if metrics.get("is_reply") and metrics.get("reply_to_user"):
            replied_to = metrics["reply_to_user"]
            interactions[replied_to][author_handle] += 1

    # Detect hidden people (interacted with by multiple S-tier accounts)
    s_tier_handles = {
        h for h, info in account_map.items()
        if info.get("priority") in ("S++", "S+")
    }

    for target_handle, interactors in interactions.items():
        s_tier_interactors = [h for h in interactors if h in s_tier_handles]
        if len(s_tier_interactors) >= 2:
            # This person is being noticed by multiple S-tier accounts
            person_id = f"person:{target_handle}"
            if person_id not in graph.entities:
                graph.entities[person_id] = Entity(
                    id=person_id,
                    name=target_handle,
                    entity_type="person",
                    metadata={
                        "hidden": True,
                        "s_tier_interactors": s_tier_interactors,
                        "interaction_count": sum(interactors.values()),
                    },
                )
                # Connect to interacting S-tier people
                for interactor in s_tier_interactors:
                    graph.add_connection(Connection(
                        source=f"person:{interactor}",
                        target=person_id,
                        relation="interacts_with",
                        weight=2.0,  # High weight for hidden discovery
                    ))

    return graph


def graph_to_json(graph: MinimalGraph) -> dict:
    """Convert graph to JSON-serializable dict."""
    return {
        "entities": {k: {
            "id": v.id, "name": v.name, "type": v.entity_type,
            "metadata": v.metadata,
        } for k, v in graph.entities.items()},
        "connections": [{
            "source": c.source, "target": c.target,
            "relation": c.relation, "weight": c.weight,
        } for c in graph.connections],
        "stats": {
            "total_entities": len(graph.entities),
            "total_connections": len(graph.connections),
            "people": len([e for e in graph.entities.values() if e.entity_type == "person"]),
            "orgs": len([e for e in graph.entities.values() if e.entity_type == "org"]),
            "topics": len([e for e in graph.entities.values() if e.entity_type == "topic"]),
            "labs": list(set(e.metadata.get("lab", "") for e in graph.entities.values() if e.entity_type == "person" and e.metadata.get("lab"))),
        },
    }


def graph_to_llm_context(graph: MinimalGraph) -> str:
    """Convert graph to text for LLM reasoning."""
    return graph.to_llm_context()
