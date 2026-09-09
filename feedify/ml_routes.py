"""ML endpoints for Feedify."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/ml", tags=["ml"])


class SignalRequest(BaseModel):
    signal_id: str
    ticker: str
    signal_score: float
    signal_type: str


class ConvergenceRequest(BaseModel):
    signals: list[dict[str, Any]]


# Source Reputation

@router.get("/reputation")
def get_reputation():
    """Get source reputation rankings."""
    from feedify.services.source_reputation import SourceReputation
    rep = SourceReputation()
    # Load from session or cache
    return {"reputations": rep.rank_accounts()}


# Signal Mapping

@router.get("/signal-mapping")
def get_signal_mapping():
    """Get signal-to-stock-movement mappings."""
    from feedify.services.signal_mapper import SignalMapper
    mapper = SignalMapper()
    return mapper.to_json()


# Convergence

@router.get("/convergence")
def get_convergence():
    """Detect convergence events."""
    from feedify.services.convergence_detector import ConvergenceDetector
    from feedify.services.frontier_graph import build_minimal_graph
    
    with SessionLocal() as session:
        graph = build_minimal_graph(session, limit=300)
    
    # Convert graph signals to list
    signals = []
    for sig in graph.signals.values():
        signals.append({
            "title": sig.summary,
            "summary": sig.interpretation,
            "lab": sig.lab,
            "author": sig.author_handle,
            "score": sig.score,
        })
    
    detector = ConvergenceDetector()
    convergences = detector.detect(signals)
    return {"convergences": convergences}
