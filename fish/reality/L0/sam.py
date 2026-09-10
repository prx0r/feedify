"""
SAM.gov Adapter - Solicitations before awards
Free key required
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class SAMGovAdapter:
    """SAM.gov API - free key required"""
    
    BASE_URL = "https://api.sam.gov"
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
    
    def search_opportunities(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        """Search opportunities before awards"""
        if not self.api_key:
            print("SAM.gov: No API key configured")
            return []
        
        url = f"{self.BASE_URL}/opportunities/v2/search?api_key={self.api_key}"
        payload = {"keyword": " ".join(keywords), "limit": limit}
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("opportunitiesData", [])
        except Exception as e:
            print(f"SAM.gov error: {e}")
            return []
    
    def to_events(self, opportunities: List[Dict]) -> List[GenericEvent]:
        events = []
        for o in opportunities:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("sam", o.get("opportunityId", "")),
                source="sam",
                source_record_id=o.get("opportunityId", ""),
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[o.get("awardee", "")],
                event_type=EventType.SOLICITATION,
                evidence=[Evidence(url=o.get("uiLink", ""))],
                confidence=0.85,
                lead_time_score=0.9,
            )
            events.append(event)
        return events


# Human task: Need SAM.gov API key from https://sam.gov
