"""
ERCOT Large-Load Queue Monitor
Free registration required, geographically restricted to US
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class ERCOTAdapter:
    """ERCOT API - free, US only"""
    
    BASE_URL = "https://www.ercot.com/api"
    
    def __init__(self):
        pass
    
    def fetch_large_load_queue(self) -> List[Dict]:
        """Fetch large-load applications"""
        # ERCOT requires registration and US IP
        # Placeholder for actual implementation
        return []
    
    def detect_status_transitions(self, loads: List[Dict]) -> List[Dict]:
        """Detect status changes in large-load queue"""
        transitions = []
        for load in loads:
            status = load.get("status", "")
            if status in ["Study Completed", "Approved", "Construction"]:
                transitions.append({
                    "entity": load.get("entity_name", ""),
                    "mw": load.get("mw_requested", 0),
                    "transition": status.lower().replace(" ", "_"),
                    "next_expected": self._next_stage(status),
                })
        return transitions
    
    def _next_stage(self, current: str) -> str:
        stages = {
            "Requested": "study_submitted",
            "Study Submitted": "study_completed",
            "Study Completed": "utility_agreement",
            "Approved": "construction",
            "Construction": "energization",
        }
        return stages.get(current, "unknown")
    
    def to_events(self, loads: List[Dict]) -> List[GenericEvent]:
        events = []
        for l in loads:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("ercot", l.get("entity_name", "")),
                source="ercot",
                source_record_id=l.get("entity_name", ""),
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[l.get("entity_name", "")],
                event_type=EventType.INTERCONNECTION_REQUEST,
                quantity=l.get("mw_requested", 0),
                unit="MW",
                evidence=[Evidence(url="https://www.ercot.com")],
                confidence=0.8,
                economic_materiality=min(l.get("mw_requested", 0) / 500, 1.0),
            )
            events.append(event)
        return events


# Human task: Need US IP and ERCOT registration
