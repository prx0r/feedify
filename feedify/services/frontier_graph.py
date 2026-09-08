"""Build the Frontier Graph from raw signals.

This transforms flat signal data into a structured graph that the LLM can reason over.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from feedify.models import Signal, SourceRecord
from feedify.services.frontier_schema import (
    Convergence,
    FrontierGraph,
    Person,
    PersonEdge,
    Post,
    Signal as FrontierSignal,
    TopicEdge,
)


def build_frontier_graph(db: Session, limit: int = 500) -> FrontierGraph:
    """Build the complete frontier graph from database signals."""
    graph = FrontierGraph()

    # Load watchlist for person metadata
    watchlist_path = Path(__file__).parent.parent.parent / "config" / "frontier_watchlist.json"
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

    for s in rows:
        if not s.record:
            continue

        metrics = s.record.metrics or {}
        author_handle = str(metrics.get("author_handle", s.record.author or ""))
        if not author_handle:
            continue

        # --- Person ---
        if author_handle not in graph.persons:
            info = account_map.get(author_handle.lower(), {})
            graph.persons[author_handle] = Person(
                handle=author_handle,
                display_name=metrics.get("author_name", ""),
                lab=info.get("lab", ""),
                role=info.get("role", ""),
                priority=info.get("priority", "A"),
                follower_count=metrics.get("author_followers", 0),
                first_seen=s.created_at.isoformat() if s.created_at else "",
                last_active=s.created_at.isoformat() if s.created_at else "",
            )
        person = graph.persons[author_handle]
        person.post_count += 1
        if s.created_at:
            person.last_active = s.created_at.isoformat()

        # --- Post ---
        post = Post(
            post_id=s.record.external_id,
            author_handle=author_handle,
            text=s.title or "",
            created_at=s.created_at.isoformat() if s.created_at else "",
            is_reply=metrics.get("is_reply", False),
            likes=metrics.get("likes", 0),
            views=metrics.get("views", 0),
            reposts=metrics.get("reposts", 0),
            url=s.record.url or "",
        )
        graph.posts[post.post_id] = post

        # --- Signal ---
        signal = FrontierSignal(
            signal_id=f"sig_{s.id}",
            post_id=post.post_id,
            author_handle=author_handle,
            signal_type=s.signal_type or "OBSERVATION",
            score=s.base_score * 100,
            summary=s.title or "",
            interpretation=s.why_it_matters or "",
            lab=person.lab,
            priority=person.priority,
            role=person.role,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        graph.signals[signal.signal_id] = signal

        # Update indexes
        graph.signals_by_author.setdefault(author_handle, []).append(signal.signal_id)
        graph.signals_by_lab.setdefault(person.lab, []).append(signal.signal_id)
        graph.posts_by_author.setdefault(author_handle, []).append(post.post_id)

    # --- Build Convergences ---
    # Group signals by topic keywords
    topic_signals: dict[str, list[str]] = {}
    for sig_id, sig in graph.signals.items():
        # Extract topic from summary
        summary_lower = sig.summary.lower()
        topics = []
        if any(t in summary_lower for t in ["qec", "error correction", "fault tolerant", "decoder"]):
            topics.append("quantum_error_correction")
        if any(t in summary_lower for t in ["rl scaling", "bigrun", "automated research", "self-improving"]):
            topics.append("agi_scaling")
        if any(t in summary_lower for t in ["reasoning", "chain of thought", "o1", "o3"]):
            topics.append("reasoning")
        if any(t in summary_lower for t in ["agent", "tool use", "coding agent"]):
            topics.append("agents")
        if any(t in summary_lower for t in ["formal verification", "theorem proving", "math"]):
            topics.append("formal_methods")
        if any(t in summary_lower for t in ["trapped ion", "ionq", "neutral atom", "infleqtion"]):
            topics.append("quantum_hardware")
        if any(t in summary_lower for t in ["superconducting", "transmon", "iqm"]):
            topics.append("superconducting")

        for topic in topics:
            topic_signals.setdefault(topic, []).append(sig_id)

    # Detect convergences (multiple labs discussing same topic within 72h)
    for topic, sig_ids in topic_signals.items():
        if len(sig_ids) < 2:
            continue

        signals = [graph.signals[sid] for sid in sig_ids if sid in graph.signals]
        labs = list(set(s.lab for s in signals if s.lab))
        handles = list(set(s.author_handle for s in signals))

        if len(labs) >= 2:  # Multi-lab convergence
            dates = [s.created_at for s in signals if s.created_at]
            first = min(dates) if dates else ""
            last = max(dates) if dates else ""

            conv = Convergence(
                convergence_id=f"conv_{topic}_{len(graph.convergences)}",
                topic=topic,
                topic_keywords=[topic],
                participants=handles,
                labs_represented=labs,
                first_signal_at=first,
                last_signal_at=last,
                signal_ids=sig_ids,
                avg_score=sum(s.score for s in signals) / len(signals),
                interpretation=f"Multiple labs ({', '.join(labs)}) discussing {topic}",
                is_regime_change=True,
                created_at=now(),
            )
            graph.convergences[conv.convergence_id] = conv
            graph.convergences_by_topic.setdefault(topic, []).append(conv.convergence_id)

    return graph


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def graph_to_llm_context(graph: FrontierGraph) -> str:
    """Convert the graph to a text context string for the LLM."""
    lines = []

    # People summary
    lines.append("## PEOPLE IN THE GRAPH")
    persons = sorted(graph.persons.values(), key=lambda p: p.follower_count, reverse=True)
    for p in persons[:30]:
        lines.append(f"- @{p.handle} ({p.lab}, {p.role}) — Priority: {p.priority}, Posts: {p.post_count}")

    # Recent signals
    lines.append("\n## RECENT SIGNALS")
    signals = sorted(graph.signals.values(), key=lambda s: s.score, reverse=True)
    for s in signals[:20]:
        lines.append(f"- [{s.signal_type}] @{s.author_handle} ({s.lab}) — Score: {s.score:.0f}/100 — {s.summary[:80]}")

    # Convergences
    if graph.convergences:
        lines.append("\n## CONVERGENCE ALERTS")
        for conv in graph.convergences.values():
            lines.append(f"- **{conv.topic}**: {', '.join(conv.participants)} ({', '.join(conv.labs_represented)}) — {conv.interpretation}")

    return "\n".join(lines)


def graph_to_json(graph: FrontierGraph) -> dict:
    """Convert graph to JSON-serializable dict."""
    return {
        "persons": {k: {
            "handle": v.handle, "display_name": v.display_name,
            "lab": v.lab, "role": v.role, "priority": v.priority,
            "follower_count": v.follower_count, "post_count": v.post_count,
        } for k, v in graph.persons.items()},
        "signals": {k: {
            "signal_id": v.signal_id, "author_handle": v.author_handle,
            "signal_type": v.signal_type, "score": v.score,
            "summary": v.summary, "lab": v.lab,
            "created_at": v.created_at,
        } for k, v in graph.signals.items()},
        "convergences": {k: {
            "convergence_id": v.convergence_id, "topic": v.topic,
            "participants": v.participants, "labs_represented": v.labs_represented,
            "interpretation": v.interpretation,
        } for k, v in graph.convergences.items()},
        "stats": {
            "total_persons": len(graph.persons),
            "total_signals": len(graph.signals),
            "total_convergences": len(graph.convergences),
            "labs": list(set(p.lab for p in graph.persons.values() if p.lab)),
        },
    }
