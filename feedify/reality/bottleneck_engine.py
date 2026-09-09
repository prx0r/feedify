"""
Bottleneck Migration Detection Engine

Detects when a solved constraint exposes a more specialized constraint underneath.

Chain:
GPU scarcity → advanced packaging → HBM yield → copper bandwidth wall → optics → 
laser/InP capacity → silicon photonics → electro-optical test → enriched uranium

Each step exposes a more specialized constraint.
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class BottleneckType(Enum):
    """Types of bottlenecks in the migration chain"""
    COMPUTE = "compute"
    PACKAGING = "packaging"
    MEMORY = "memory"
    BANDWIDTH = "bandwidth"
    OPTICS = "optics"
    LASER = "laser"
    ENERGY = "energy"
    FUEL = "fuel"
    MATERIALS = "materials"
    TESTING = "testing"
    TALENT = "talent"


@dataclass
class BottleneckNode:
    """A node in the bottleneck migration chain"""
    type: BottleneckType
    name: str
    description: str
    companies: List[str]  # Who owns this bottleneck
    evidence_level: float  # 0-1
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    next_bottleneck: Optional['BottleneckNode'] = None


@dataclass
class MigrationEvent:
    """A detected bottleneck migration"""
    from_bottleneck: BottleneckNode
    to_bottleneck: BottleneckNode
    trigger: str  # What caused the migration
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.5


class BottleneckMigrationEngine:
    """Detects bottleneck migrations"""
    
    # The canonical bottleneck chain
    CANONICAL_CHAIN = [
        BottleneckNode(
            type=BottleneckType.COMPUTE,
            name="GPU Scarcity",
            description="AI models need more GPUs than available",
            companies=["NVDA", "AMD", "INTC"],
            evidence_level=0.9
        ),
        BottleneckNode(
            type=BottleneckType.PACKAGING,
            name="Advanced Packaging",
            description="CoWoS, HBM packaging capacity constrained",
            companies=["TSM", "AMKR", "SUSS"],
            evidence_level=0.85
        ),
        BottleneckNode(
            type=BottleneckType.MEMORY,
            name="HBM Yield",
            description="High Bandwidth Memory production yield",
            companies=["SKHY", "MU", "Samsung"],
            evidence_level=0.8
        ),
        BottleneckNode(
            type=BottleneckType.BANDWIDTH,
            name="Copper Bandwidth Wall",
            description="Electrical interconnect hitting physical limits",
            companies=["MRVL", "AVGO"],
            evidence_level=0.75
        ),
        BottleneckNode(
            type=BottleneckType.OPTICS,
            name="Optical Interconnect",
            description="Silicon photonics for data center",
            companies=["COHR", "LITE", "IIVI"],
            evidence_level=0.7
        ),
        BottleneckNode(
            type=BottleneckType.LASER,
            name="Laser/InP Capacity",
            description="InP laser production capacity",
            companies=["COHR", "LITE", "SIVE"],
            evidence_level=0.65
        ),
        BottleneckNode(
            type=BottleneckType.TESTING,
            name="Electro-Optical Test",
            description="Testing and inspection for photonics",
            companies=["ONTO", "FORM", "VIAV"],
            evidence_level=0.6
        ),
        BottleneckNode(
            type=BottleneckType.FUEL,
            name="Enriched Uranium",
            description="HALEU for advanced nuclear",
            companies=["LEU", "STDN"],
            evidence_level=0.55
        ),
        BottleneckNode(
            type=BottleneckType.ENERGY,
            name="Power Generation",
            description="Electricity for data centers",
            companies=["CEG", "VST", "TLN"],
            evidence_level=0.5
        ),
        BottleneckNode(
            type=BottleneckType.MATERIALS,
            name="Critical Materials",
            description="Rare materials for chips/reactors",
            companies=["MP", "ALB", "LTHM"],
            evidence_level=0.45
        ),
    ]
    
    def __init__(self):
        self.events: List[MigrationEvent] = []
        self.current_bottleneck = self.CANONICAL_CHAIN[0]
    
    def detect_migration(self, evidence: Dict) -> Optional[MigrationEvent]:
        """Detect if evidence suggests a bottleneck migration"""
        
        # Check if evidence relates to current bottleneck
        if self._matches_bottleneck(evidence, self.current_bottleneck):
            # Check if it resolves the current bottleneck
            if self._resolves_bottleneck(evidence):
                # Find next bottleneck
                next_bottleneck = self._find_next_bottleneck()
                if next_bottleneck:
                    event = MigrationEvent(
                        from_bottleneck=self.current_bottleneck,
                        to_bottleneck=next_bottleneck,
                        trigger=evidence.get("description", ""),
                        confidence=evidence.get("confidence", 0.5)
                    )
                    self.events.append(event)
                    self.current_bottleneck = next_bottleneck
                    return event
        
        return None
    
    def _matches_bottleneck(self, evidence: Dict, bottleneck: BottleneckNode) -> bool:
        """Check if evidence relates to a bottleneck"""
        evidence_text = str(evidence).lower()
        
        # Simple keyword matching
        keywords = {
            BottleneckType.COMPUTE: ["gpu", "nvidia", "amd", "compute", "ai chip"],
            BottleneckType.PACKAGING: ["cowos", "packaging", "advanced packaging", "osat"],
            BottleneckType.MEMORY: ["hbm", "memory", "dram", "sk hynix", "micron"],
            BottleneckType.BANDWIDTH: ["interconnect", "bandwidth", "copper", "signal"],
            BottleneckType.OPTICS: ["photonics", "optical", "silicon photonics", "lidar"],
            BottleneckType.LASER: ["laser", "inp", "indium phosphide", "cw laser"],
            BottleneckType.TESTING: ["test", "inspection", "metrology", "probe"],
            BottleneckType.FUEL: ["uranium", "haleu", "enrichment", "nuclear fuel"],
            BottleneckType.ENERGY: ["power", "electricity", "grid", "transformer"],
            BottleneckType.MATERIALS: ["rare earth", "lithium", "gallium", "germanium"],
        }
        
        return any(kw in evidence_text for kw in keywords.get(bottleneck.type, []))
    
    def _resolves_bottleneck(self, evidence: Dict) -> bool:
        """Check if evidence resolves a bottleneck"""
        resolution_keywords = [
            "capacity expansion", "new facility", "production start",
            "revenue recognition", "contract awarded", "funding secured"
        ]
        return any(kw in str(evidence).lower() for kw in resolution_keywords)
    
    def _find_next_bottleneck(self) -> Optional[BottleneckNode]:
        """Find the next bottleneck in the chain"""
        for i, node in enumerate(self.CANONICAL_CHAIN):
            if node == self.current_bottleneck and i + 1 < len(self.CANONICAL_CHAIN):
                return self.CANONICAL_CHAIN[i + 1]
        return None
    
    def get_migration_history(self) -> List[Dict]:
        """Get history of detected migrations"""
        return [
            {
                "from": e.from_bottleneck.name,
                "to": e.to_bottleneck.name,
                "trigger": e.trigger,
                "timestamp": e.timestamp.isoformat(),
                "confidence": e.confidence
            }
            for e in self.events
        ]
    
    def get_current_opportunities(self) -> List[Dict]:
        """Get investment opportunities at current bottleneck"""
        return [
            {
                "company": c,
                "bottleneck": self.current_bottleneck.name,
                "evidence_level": self.current_bottleneck.evidence_level
            }
            for c in self.current_bottleneck.companies
        ]
