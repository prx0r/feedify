"""Minimal graph — entities + connections only.

No fancy schemas. Just:
- Entity: id, name, type, metadata
- Connection: source, target, relation, weight, evidence

The LLM does the semantic intelligence.
The graph gives memory, neighborhood, provenance, cheap numerical signals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    """A person, org, topic, or technology."""
    id: str
    name: str
    entity_type: str  # person, org, topic, technology
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Connection:
    """A relationship between two entities."""
    source: str
    target: str
    relation: str  # works_at, interacts_with, works_on, mentions, related_to
    weight: float = 1.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MinimalGraph:
    """The simplest possible intelligence graph."""
    entities: dict[str, Entity] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)

    # Indexes for fast lookup
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
        """Get all entities connected to this entity."""
        neighbors = []
        for idx in self.connections_by_source.get(entity_id, []):
            conn = self.connections[idx]
            target = self.entities.get(conn.target)
            if target:
                neighbors.append({
                    "entity": target,
                    "relation": conn.relation,
                    "weight": conn.weight,
                })
        for idx in self.connections_by_target.get(entity_id, []):
            conn = self.connections[idx]
            source = self.entities.get(conn.source)
            if source:
                neighbors.append({
                    "entity": source,
                    "relation": conn.relation,
                    "weight": conn.weight,
                })
        return neighbors

    def get_entity_connections(self, entity_id: str) -> list[Connection]:
        """Get all connections involving this entity."""
        connections = []
        for idx in self.connections_by_source.get(entity_id, []):
            connections.append(self.connections[idx])
        for idx in self.connections_by_target.get(entity_id, []):
            connections.append(self.connections[idx])
        return connections

    def to_llm_context(self) -> str:
        """Convert graph to text for LLM reasoning."""
        lines = []

        # Entities by type
        people = [e for e in self.entities.values() if e.entity_type == "person"]
        orgs = [e for e in self.entities.values() if e.entity_type == "org"]
        topics = [e for e in self.entities.values() if e.entity_type == "topic"]

        if people:
            lines.append("## PEOPLE")
            for p in people:
                lab = p.metadata.get("lab", "")
                role = p.metadata.get("role", "")
                priority = p.metadata.get("priority", "")
                lines.append(f"- @{p.name} ({lab}, {role}) — Priority: {priority}")

        if orgs:
            lines.append("\n## ORGANIZATIONS")
            for o in orgs:
                lines.append(f"- {o.name}")

        if topics:
            lines.append("\n## TOPICS")
            for t in topics:
                lines.append(f"- {t.name}")

        # Connections summary
        if self.connections:
            lines.append(f"\n## CONNECTIONS ({len(self.connections)} total)")
            # Show strongest connections
            sorted_conns = sorted(self.connections, key=lambda c: c.weight, reverse=True)
            for conn in sorted_conns[:20]:
                source = self.entities.get(conn.source)
                target = self.entities.get(conn.target)
                if source and target:
                    lines.append(f"- {source.name} → {conn.relation} → {target.name} (weight: {conn.weight:.1f})")

        return "\n".join(lines)
