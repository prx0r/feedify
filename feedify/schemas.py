from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NormalizedItem(BaseModel):
    """Adapter output contract. Unchanged — adapters produce this."""
    source_type: str
    external_id: str
    title: str
    url: str | None = None
    body: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class ObjectDraft(BaseModel):
    """What the semantic compiler produces from an artifact.
    Replaces SignalDraft. These become Objects in the graph."""
    object_key: str
    kind: str = "idea"
    title: str
    summary: str
    confidence: float = 0.5
    domain: str = "general"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EdgeDraft(BaseModel):
    """A relationship the compiler discovers between objects."""
    source_key: str
    target_key: str
    relation: str = "related_to"
    weight: float = 1.0
    evidence_artifact_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedCreate(BaseModel):
    name: str
    prompt: str = ""
    description: str = ""
    slug: str | None = None
    public: bool = True
    icon: str = "⚡"
    weights: dict[str, float] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)


class FeedUpdate(BaseModel):
    name: str | None = None
    prompt: str | None = None
    description: str | None = None
    public: bool | None = None
    icon: str | None = None
    weights: dict[str, float] | None = None
    filters: dict[str, Any] | None = None
