"""Build the Minimal Graph from DB Objects and Edges.

The graph is now backed by the Object + Edge tables.
This module provides the build function for LLM context generation.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from feedify.models import Object, Edge
from feedify.services.minimal_graph import Connection, Entity, MinimalGraph


def build_minimal_graph(db: Session, limit: int = 500) -> MinimalGraph:
    """Build the minimal intelligence graph from DB Objects and Edges."""
    graph = MinimalGraph()

    objects = db.scalars(select(Object).limit(limit)).all()
    for obj in objects:
        entity = Entity(
            id=obj.object_key,
            name=obj.title,
            entity_type=obj.kind,
            metadata={
                "summary": obj.summary,
                "confidence": obj.confidence,
                "domain": obj.domain,
                "version": obj.version,
                **(obj.metadata_json or {}),
            },
        )
        graph.add_entity(entity)

    edges = db.scalars(select(Edge).limit(limit * 3)).all()
    for edge in edges:
        source_obj = db.get(Object, edge.source_id)
        target_obj = db.get(Object, edge.target_id)
        if source_obj and target_obj:
            conn = Connection(
                source=source_obj.object_key,
                target=target_obj.object_key,
                relation=edge.relation,
                weight=edge.weight,
                evidence_ids=[str(edge.evidence_artifact_id)] if edge.evidence_artifact_id else [],
                metadata=edge.metadata_json or {},
            )
            graph.add_connection(conn)

    return graph


def graph_to_json(graph: MinimalGraph) -> dict:
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
            "companies": len([e for e in graph.entities.values() if e.entity_type in ("company", "org")]),
            "theories": len([e for e in graph.entities.values() if e.entity_type in ("theory", "idea", "claim")]),
        },
    }


def graph_to_llm_context(graph: MinimalGraph) -> str:
    return graph.to_llm_context()
