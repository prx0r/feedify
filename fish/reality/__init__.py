"""
Reality Feed: The Canonical Intelligence Hierarchy

L0: Reality (permits, licenses, contracts, transactions, revenues, construction, production)
L1: Technical Frontier (GitHub, papers, patents, standards)
L2: Institutional Intent (government awards, utility plans, fund holdings, insiders)
L3: Expert Interpretation (Keller, Xinyu, Dylan, Handmer, Marblestone)
L4: Narrative (X, Reddit, news, analysts)

Most financial products run L4 → L3.
We run L0 → L1 → L2 → L3 → L4.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class EvidenceLevel(Enum):
    """State transition scoring - every transition increases evidence"""
    IDEA = 1           # Rumor, hypothesis
    PAPER = 2          # Published research, whitepaper
    PATENT = 3         # IP filed or acquired
    PROTOTYPE = 4      # Working demo
    GRANT = 5          # Government funding awarded
    QUALIFICATION = 6  # Customer testing/qualification
    PERMIT = 7         # Physical permits filed
    PURCHASE_ORDER = 8 # Contracts signed
    CAPACITY_EXPANSION = 9  # Building/expanding
    PRODUCTION = 10    # Making product
    REVENUE = 11       # Recognizing revenue


class SourceType(Enum):
    """The 10 subfeeds"""
    UTILITY_DOCKETS = "utility_dockets"
    ASIAN_DISCLOSURES = "asian_disclosures"
    SEC_ECONOMIC_EVENT = "sec_economic_event"
    GOVERNMENT_PROCUREMENT = "government_procurement"
    NRC_DOE_NUCLEAR = "nrc_doe_nuclear"
    PHYSICAL_PERMITS = "physical_permits"
    PATENT_ASSIGNMENT = "patent_assignment"
    FERC_EIA_PLANT = "ferc_eia_plant"
    GITHUB_CAPABILITY = "github_capability"
    PRECURSOR_HUMAN = "precursor_human"


@dataclass
class StateTransition:
    """Tracks state changes for evidence-weighted scoring"""
    entity: str  # Company, technology, concept
    from_state: EvidenceLevel
    to_state: EvidenceLevel
    source: SourceType
    timestamp: datetime
    evidence_url: Optional[str] = None
    evidence_text: Optional[str] = None
    confidence: float = 0.5  # 0-1
    
    @property
    def transition_score(self) -> float:
        """Score based on state transition magnitude"""
        return (self.to_state.value - self.from_state.value) * self.confidence


@dataclass
class BottleneckSignal:
    """Detected bottleneck before market recognition"""
    concept: str  # What's becoming scarce
    evidence_level: EvidenceLevel
    sources: List[SourceType]  # Independent sources confirming
    entities: List[str]  # Companies that own the bottleneck
    lead_time_months: float  # How far ahead of consensus
    confidence: float  # 0-1
    detected_at: datetime = field(default_factory=datetime.now)
    
    @property
    def convergence_score(self) -> float:
        """Score based on independent source convergence"""
        return len(set(self.sources)) * self.confidence


@dataclass
class RealityEvent:
    """A real-world event detected from primary sources"""
    source_type: SourceType
    source_url: str
    entity: str
    event_type: str  # "permit", "contract", "revenue", "patent", etc.
    event_data: dict
    evidence_level: EvidenceLevel
    timestamp: datetime
    raw_text: Optional[str] = None
    
    def to_signal(self) -> BottleneckSignal:
        """Convert reality event to bottleneck signal"""
        return BottleneckSignal(
            concept=self.event_type,
            evidence_level=self.evidence_level,
            sources=[self.source_type],
            entities=[self.entity],
            lead_time_months=0,
            confidence=0.5
        )
