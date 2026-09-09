"""
USAspending Adapter - Federal awards, no key required
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class USAspendingAdapter:
    """USAspending API - free, no auth"""
    
    BASE_URL = "https://api.usaspending.gov"
    
    def search_awards(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        """Search federal awards"""
        url = f"{self.BASE_URL}/api/v2/search/spending_by_award/"
        payload = {
            "filters": {
                "keywords": keywords,
                "time_period": [{"start_date": "2024-01-01", "end_date": "2026-12-31"}]
            },
            "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", "Description", "Start Date"],
            "limit": limit,
            "page": 1
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("results", [])
        except Exception as e:
            print(f"USAspending error: {e}")
            return []
    
    def to_events(self, awards: List[Dict]) -> List[GenericEvent]:
        """Convert to generic events"""
        events = []
        for a in awards:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("usaspending", a.get("Award ID", "")),
                source="usaspending",
                source_record_id=a.get("Award ID", ""),
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[a.get("Recipient Name", "")],
                event_type=EventType.AWARD,
                value=a.get("Award Amount", 0),
                currency="USD",
                evidence=[Evidence(url=f"https://www.usaspending.gov/award/{a.get('Award ID', '')}")],
                confidence=0.9,
                economic_materiality=min(a.get("Award Amount", 0) / 10000000, 1.0),
            )
            events.append(event)
        return events


# Human task: No key needed, works now
