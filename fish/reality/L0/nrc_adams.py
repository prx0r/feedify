"""
NRC ADAMS Adapter - Nuclear licensing
Free account required (released Dec 2025)
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class NRCADAMSAdapter:
    """NRC ADAMS API - free account required"""
    
    BASE_URL = "https://adams-developer.nrc.gov/api/v1"
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
    
    def search_documents(self, query: str, limit: int = 50) -> List[Dict]:
        """Search ADAMS documents"""
        if not self.api_key:
            print("NRC ADAMS: No API key configured")
            return []
        
        url = f"{self.BASE_URL}/search?query={query}&accession_number=&date_range=&mlist=&docket=&category=&page_size={limit}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("results", [])
        except Exception as e:
            print(f"NRC ADAMS error: {e}")
            return []
    
    def get_licensing_status(self, docket_id: str) -> Dict:
        """Get licensing status for a docket"""
        docs = self.search_documents(f"docket:{docket_id}")
        
        # Map document types to licensing stages
        stages = {
            "License Application": EventType.APPLICATION,
            "RAI": EventType.REGULATORY_QUESTIONS,
            "Safety Evaluation": EventType.NUCLEAR_APPROVAL,
            "License": EventType.NUCLEAR_APPROVAL,
            "Amendment": EventType.OPTION_EXERCISED,
            "Inspection": EventType.OPERATION,
        }
        
        return {
            "docket": docket_id,
            "documents": len(docs),
            "latest": docs[0] if docs else None,
        }
    
    def to_events(self, documents: List[Dict]) -> List[GenericEvent]:
        events = []
        for d in documents:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("nrc_adams", d.get("accession_number", "")),
                source="nrc_adams",
                source_record_id=d.get("accession_number", ""),
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[d.get("docket_id", "")],
                event_type=EventType.APPLICATION,
                evidence=[Evidence(url=d.get("url", ""))],
                confidence=0.85,
                lead_time_score=0.9,
            )
            events.append(event)
        return events


# Human task: Need NRC ADAMS API key from https://adams-api-developer.nrc.gov
