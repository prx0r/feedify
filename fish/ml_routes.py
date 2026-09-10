"""ML endpoints for Feedify 2.0."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from fish.db import SessionLocal

router = APIRouter(prefix="/api/ml", tags=["ml"])


class SignalRequest(BaseModel):
    object_id: int
    ticker: str
    signal_score: float
    kind: str


class ConvergenceRequest(BaseModel):
    signals: list[dict[str, Any]]


@router.get("/reputation")
def get_reputation():
    """Get source reputation rankings."""
    from fish.services.source_reputation import SourceReputation
    rep = SourceReputation()
    return {"reputations": rep.rank_accounts()}


@router.get("/signal-mapping")
def get_signal_mapping():
    """Get signal-to-stock-movement mappings."""
    from fish.services.signal_mapper import SignalMapper
    mapper = SignalMapper()
    return mapper.to_json()


@router.get("/convergence")
def get_convergence():
    """Detect convergence events from the knowledge graph."""
    from fish.services.convergence_detector import ConvergenceDetector

    with SessionLocal() as session:
        objects = session.scalars(
            select(Object).where(Object.kind.in_(["claim", "theory", "idea"])).limit(200)
        ).all()

    signals = []
    for obj in objects:
        signals.append({
            "title": obj.title,
            "summary": obj.summary,
            "domain": obj.domain,
            "confidence": obj.confidence,
        })

    detector = ConvergenceDetector()
    convergences = detector.detect(signals)
    return {"convergences": convergences}
