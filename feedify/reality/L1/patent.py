"""
Patent Adapter - USPTO + EPO OPS
USPTO: Free bulk downloads
EPO OPS: 4GB/week free
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class USPTOAdapter:
    """USPTO Patent Assignment Search"""
    
    BASE_URL = "https://assignmentcenter.uspto.gov/api"
    
    def search_assignments(self, assignor: str = None, assignee: str = None) -> List[Dict]:
        """Search patent assignments"""
        # USPTO assignment center
        return []
    
    def detect_ip_transfer(self, assignments: List[Dict]) -> List[Dict]:
        """Detect IP being acquired/transferred"""
        transfers = []
        for a in assignments:
            if a.get("assignor") != a.get("assignee"):
                transfers.append({
                    "patent": a.get("patent_number", ""),
                    "from": a.get("assignor", ""),
                    "to": a.get("assignee", ""),
                    "date": a.get("date_recorded", ""),
                })
        return transfers


class EPOOPSAdapter:
    """EPO Open Patent Services - 4GB/week free"""
    
    BASE_URL = "https://ops.epo.org/3.2/rest-services"
    
    def __init__(self):
        pass
    
    def search_patents(self, query: str, limit: int = 10) -> List[Dict]:
        """Search patents"""
        # EPO OPS requires authentication token
        # Placeholder
        return []
    
    def get_patent_family(self, patent_id: str) -> List[Dict]:
        """Get patent family"""
        return []


class PatentAdapter:
    """Unified patent adapter"""
    
    def __init__(self):
        self.uspto = USPTOAdapter()
        self.epo = EPOOPSAdapter()
    
    def detect_convergence(self, technology: str) -> Dict:
        """Detect when multiple companies converge on same technology"""
        return {"technology": technology, "convergence": []}
    
    def to_events(self, patents: List[Dict]) -> List[GenericEvent]:
        events = []
        for p in patents:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("patent", p.get("patent_number", "")),
                source="patent",
                source_record_id=p.get("patent_number", ""),
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[p.get("assignee", "")],
                technology_ids=[p.get("technology", "")],
                event_type=EventType.PATENT_APPLICATION,
                evidence=[Evidence(url=p.get("url", ""))],
                confidence=0.7,
            )
            events.append(event)
        return events


# Human task: USPTO bulk is free, EPO OPS needs auth token
