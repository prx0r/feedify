"""Minimal graph — DB-backed entities + edges.

The graph is stored in PostgreSQL/SQLite as Object + Edge tables.
This module builds the in-memory MinimalGraph from the DB for LLM context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from feedify.models import Object as ObjectModel, Edge as EdgeModel


@dataclass
class Entity:
    """A person, org, topic, or technology."""
    id: str
    name: str
    entity_type: str  # maps from Object.kind
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Connection:
    """A relationship between two entities."""
    source: str
    target: str
    relation: str
    weight: float = 1.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MinimalGraph:
    """The simplest possible intelligence graph. Built from DB."""
    entities: dict[str, Entity] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    connections_by_source: dict[str, list[int]] = field(default_factory=dict)
    connections_by_target: dict[str, list[int]] = field(default_factory=dict)
    connections_by_relation: dict[str, list[int]] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def add_connection(self, conn: Connection) -> None:
        idx = len(self.connections)
        self.connections.append(conn)
        self.connections_by_source.setdefault(conn.source, []).append(idx)
        self.connections_by_target.setdefault(conn.target, []).append(idx)
        self.connections_by_relation.setdefault(conn.relation, []).append(idx)

    def get_neighbors(self, entity_id: str) -> list[dict[str, Any]]:
        neighbors = []
        for idx in self.connections_by_source.get(entity_id, []):
            conn = self.connections[idx]
            target = self.entities.get(conn.target)
            if target:
                neighbors.append({"entity": target, "relation": conn.relation, "weight": conn.weight})
        for idx in self.connections_by_target.get(entity_id, []):
            conn = self.connections[idx]
            source = self.entities.get(conn.source)
            if source:
                neighbors.append({"entity": source, "relation": conn.relation, "weight": conn.weight})
        return neighbors

    def get_entity_connections(self, entity_id: str) -> list[Connection]:
        connections = []
        for idx in self.connections_by_source.get(entity_id, []):
            connections.append(self.connections[idx])
        for idx in self.connections_by_target.get(entity_id, []):
            connections.append(self.connections[idx])
        return connections

    def to_llm_context(self) -> str:
        lines = []
        people = [e for e in self.entities.values() if e.entity_type == "person"]
        companies = [e for e in self.entities.values() if e.entity_type in ("company", "org")]
        theories = [e for e in self.entities.values() if e.entity_type in ("theory", "idea", "claim")]
        technologies = [e for e in self.entities.values() if e.entity_type == "technology"]

        if people:
            lines.append("## PEOPLE")
            for p in people:
                lines.append(f"- {p.name} — {p.metadata.get('summary', '')}")

        if companies:
            lines.append("\n## COMPANIES")
            for c in companies:
                lines.append(f"- {c.name} — {c.metadata.get('summary', '')}")

        if theories:
            lines.append("\n## THEORIES & IDEAS")
            for t in theories:
                lines.append(f"- {t.name} — {t.metadata.get('summary', '')}")

        if technologies:
            lines.append("\n## TECHNOLOGIES")
            for t in technologies:
                lines.append(f"- {t.name} — {t.metadata.get('summary', '')}")

        if self.connections:
            lines.append(f"\n## CONNECTIONS ({len(self.connections)} total)")
            sorted_conns = sorted(self.connections, key=lambda c: c.weight, reverse=True)
            for conn in sorted_conns[:30]:
                source = self.entities.get(conn.source)
                target = self.entities.get(conn.target)
                if source and target:
                    lines.append(f"- {source.name} → {conn.relation} → {target.name} (weight: {conn.weight:.1f})")

        return "\n".join(lines)


def build_graph_from_db(session: Session, limit: int = 500) -> MinimalGraph:
    """Build a MinimalGraph from the DB-backed Object and Edge tables."""
    graph = MinimalGraph()

    objects = session.scalars(select(ObjectModel).limit(limit)).all()
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

    edges = session.scalars(select(EdgeModel).limit(limit * 3)).all()
    for edge in edges:
        source_obj = session.get(ObjectModel, edge.source_id)
        target_obj = session.get(ObjectModel, edge.target_id)
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
