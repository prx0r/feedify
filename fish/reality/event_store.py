"""
Generic Event Schema - Immutable Event Store

All sources normalize to this schema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import json
import hashlib


class EventType(Enum):
    """State transition types"""
    # Research
    IDEA = "idea"
    PAPER = "paper"
    INDEPENDENT_REPRODUCTION = "independent_reproduction"
    
    # IP
    PATENT_APPLICATION = "patent_application"
    PATENT_GRANT = "patent_grant"
    PATENT_ASSIGNMENT = "patent_assignment"
    
    # Government
    RFI = "rfi"
    SOLICITATION = "solicitation"
    LOI = "loi"
    AWARD = "award"
    OPTION_EXERCISED = "option_exercised"
    
    # Corporate
    PIPELINE = "pipeline"
    QUALIFICATION = "qualification"
    ORDER = "order"
    BACKLOG = "backlog"
    SHIPMENT = "shipment"
    REVENUE = "revenue"
    CASH = "cash"
    
    # Physical
    PLANNING_APPLICATION = "planning_application"
    PERMIT = "permit"
    INTERCONNECTION_REQUEST = "interconnection_request"
    APPROVED = "approved"
    CONSTRUCTION = "construction"
    COMMISSIONING = "commissioning"
    PRODUCTION = "production"
    
    # Nuclear
    PRE_APPLICATION = "pre_application"
    APPLICATION = "application"
    REGULATORY_QUESTIONS = "regulatory_questions"
    NUCLEAR_APPROVAL = "nuclear_approval"
    FUEL_ALLOCATION = "fuel_allocation"
    FUEL_FABRICATION = "fuel_fabrication"
    OPERATION = "operation"


@dataclass
class Evidence:
    """Evidence reference"""
    url: str
    document_hash: Optional[str] = None
    excerpt: Optional[str] = None
    primary_source: bool = True


@dataclass
class GenericEvent:
    """Normalized event from any source"""
    event_id: str
    source: str
    source_record_id: str
    
    observed_at: datetime
    effective_at: datetime
    
    entity_ids: List[str]
    event_type: EventType
    
    counterparty_ids: List[str] = field(default_factory=list)
    technology_ids: List[str] = field(default_factory=list)
    geo_ids: List[str] = field(default_factory=list)
    
    state_before: Optional[str] = None
    state_after: Optional[str] = None
    
    quantity: Optional[float] = None
    unit: Optional[str] = None
    value: Optional[float] = None
    currency: Optional[str] = None
    
    evidence: List[Evidence] = field(default_factory=list)
    
    confidence: float = 0.5
    novelty: float = 0.5
    economic_materiality: float = 0.5
    lead_time_score: float = 0.0
    
    raw_data: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "event_id": self.event_id,
            "source": self.source,
            "source_record_id": self.source_record_id,
            "observed_at": self.observed_at.isoformat(),
            "effective_at": self.effective_at.isoformat(),
            "entity_ids": self.entity_ids,
            "counterparty_ids": self.counterparty_ids,
            "technology_ids": self.technology_ids,
            "geo_ids": self.geo_ids,
            "event_type": self.event_type.value,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "quantity": self.quantity,
            "unit": self.unit,
            "value": self.value,
            "currency": self.currency,
            "evidence": [{"url": e.url, "excerpt": e.excerpt} for e in self.evidence],
            "confidence": self.confidence,
            "novelty": self.novelty,
            "economic_materiality": self.economic_materiality,
            "lead_time_score": self.lead_time_score,
        }
    
    @staticmethod
    def generate_id(source: str, record_id: str) -> str:
        """Generate deterministic event ID"""
        raw = f"{source}:{record_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class EventStore:
    """Immutable event store"""
    
    def __init__(self, db_path: str = "data/events.jsonl"):
        self.db_path = db_path
    
    def append(self, event: GenericEvent):
        """Append event to store (immutable)"""
        with open(self.db_path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
    
    def query(self, source: str = None, event_type: EventType = None, 
              entity_id: str = None, limit: int = 100) -> List[dict]:
        """Query events"""
        results = []
        try:
            with open(self.db_path, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    
                    if source and event["source"] != source:
                        continue
                    if event_type and event["event_type"] != event_type.value:
                        continue
                    if entity_id and entity_id not in event["entity_ids"]:
                        continue
                    
                    results.append(event)
                    
                    if len(results) >= limit:
                        break
        except FileNotFoundError:
            pass
        
        return results
