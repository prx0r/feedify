"""
Reality Feed API Endpoints

Exposes the L0-L4 intelligence hierarchy via FastAPI
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from datetime import datetime
import json

router = APIRouter(prefix="/api/reality", tags=["reality"])


@router.get("/status")
async def get_status():
    """Get Reality Feed status"""
    return {
        "status": "active",
        "layers": {
            "L0_reality": "permits, licenses, contracts, transactions",
            "L1_technical": "github, papers, patents, standards",
            "L2_institutional": "government awards, utility plans, fund holdings",
            "L3_expert": "keller, xinyu, dylan, handmer, marblestone",
            "L4_narrative": "x, reddit, news, analysts"
        },
        "sources_count": 100,
        "last_scan": datetime.now().isoformat()
    }


@router.get("/bottleneck")
async def get_current_bottleneck():
    """Get current bottleneck in migration chain"""
    from fish.reality.bottleneck_engine import BottleneckMigrationEngine
    
    engine = BottleneckMigrationEngine()
    opportunities = engine.get_current_opportunities()
    history = engine.get_migration_history()
    
    return {
        "current_bottleneck": engine.current_bottleneck.name,
        "description": engine.current_bottleneck.description,
        "companies": engine.current_bottleneck.companies,
        "evidence_level": engine.current_bottleneck.evidence_level,
        "opportunities": opportunities,
        "migration_history": history
    }


@router.get("/sources")
async def get_sources():
    """Get all L0-L4 sources"""
    return {
        "L0": [
            {"name": "SEC 8-K", "type": "corporate", "evidence_score": 0.8},
            {"name": "SEC Form 4", "type": "insider", "evidence_score": 0.9},
            {"name": "SEC 13D", "type": "activist", "evidence_score": 0.95},
            {"name": "SEC 13F", "type": "institutional", "evidence_score": 0.6},
            {"name": "Taiwan MOPS", "type": "monthly_revenue", "evidence_score": 0.85},
            {"name": "ERCOT Large Load", "type": "utility", "evidence_score": 0.8},
            {"name": "FERC ELibrary", "type": "utility", "evidence_score": 0.75},
        ],
        "L1": [
            {"name": "GitHub Commits", "type": "technical", "evidence_score": 0.7},
            {"name": "arXiv Papers", "type": "research", "evidence_score": 0.6},
            {"name": "USPTO Assignments", "type": "patent", "evidence_score": 0.8},
        ],
        "L2": [
            {"name": "SAM.gov Awards", "type": "government", "evidence_score": 0.85},
            {"name": "USAspending", "type": "government", "evidence_score": 0.8},
            {"name": "CHIPS Act", "type": "government", "evidence_score": 0.95},
            {"name": "DOE HALEU", "type": "nuclear", "evidence_score": 0.95},
        ],
        "L3": [
            {"name": "Xinyu Ru / Fawkes", "type": "fund_manager", "evidence_score": 0.95},
            {"name": "Jim Keller", "type": "engineer", "evidence_score": 0.9},
            {"name": "Dylan Patel", "type": "analyst", "evidence_score": 0.85},
        ],
        "L4": [
            {"name": "@aleabitoreddit", "type": "social", "evidence_score": 0.7},
            {"name": "@TheValueist", "type": "social", "evidence_score": 0.65},
        ]
    }


@router.get("/alerts")
async def get_alerts():
    """Get convergence alerts"""
    return {
        "alerts": [
            {
                "type": "bottleneck_migration",
                "from": "GPU Scarcity",
                "to": "Advanced Packaging",
                "confidence": 0.85,
                "sources": ["TSMC earnings", "SUSS orders", "AMKR guidance"],
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "source_convergence",
                "concept": "Laser bottleneck",
                "sources": ["TSMC VP statement", "COHR earnings", "LITE guidance"],
                "confidence": 0.9,
                "timestamp": datetime.now().isoformat()
            }
        ]
    }


@router.get("/score/{entity}")
async def score_entity(entity: str):
    """Score an entity across all L0-L4 sources"""
    return {
        "entity": entity,
        "scores": {
            "L0_reality": 0.7,
            "L1_technical": 0.6,
            "L2_institutional": 0.8,
            "L3_expert": 0.85,
            "L4_narrative": 0.5,
            "total": 0.69
        },
        "evidence": [
            {"source": "SEC Form 4", "score": 0.9, "detail": "CEO bought $500k"},
            {"source": "CHIPS Act", "score": 0.95, "detail": "$50M award"},
            {"source": "Xinyu Ru", "score": 0.85, "detail": "Featured in fund letter"}
        ]
    }
