from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NormalizedItem(BaseModel):
    source_type: str
    external_id: str
    title: str
    url: str | None = None
    body: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class SignalDraft(BaseModel):
    signal_type: str
    domain: str = "general"
    title: str
    summary: str
    why_it_matters: str = ""
    novelty: float = 0.5
    actionability: float = 0.5
    source_proximity: float = 0.5
    confidence: float = 0.5
    evidence_strength: float = 0.5
    tags: list[str] = Field(default_factory=list)
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
