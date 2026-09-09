"""
PUDL Integration - EIA/FERC/EPA energy data
Uses public S3 bucket, no key needed
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class PUDLAdapter:
    """PUDL - public energy data"""
    
    S3_URL = "https://s3.catalyst.coop/pudl"
    
    def __init__(self):
        pass
    
    def fetch_eia923(self, year: int = 2025) -> List[Dict]:
        """Fetch EIA-923 plant-level data"""
        # PUDL hosts Parquet files on S3
        # For now, return structure
        return []
    
    def fetch_ferc1(self, year: int = 2025) -> List[Dict]:
        """Fetch FERC Form 1 data"""
        return []
    
    def detect_generation_changes(self, plant_data: List[Dict]) -> List[Dict]:
        """Detect changes in generation patterns"""
        changes = []
        for p in plant_data:
            if p.get("net_generation_mwh", 0) > 1000000:  # Large plants
                changes.append({
                    "plant": p.get("plant_name", ""),
                    "generation_mwh": p.get("net_generation_mwh", 0),
                    "fuel": p.get("fuel_type", ""),
                })
        return changes
    
    def to_events(self, data: List[Dict]) -> List[GenericEvent]:
        events = []
        for d in data:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("pudl", d.get("plant_id", "")),
                source="pudl",
                source_record_id=str(d.get("plant_id", "")),
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[d.get("plant_name", "")],
                event_type=EventType.PRODUCTION,
                quantity=d.get("net_generation_mwh", 0),
                unit="MWh",
                evidence=[Evidence(url="https://s3.catalyst.coop/pudl")],
                confidence=0.85,
            )
            events.append(event)
        return events


# Human task: PUDL is free on S3, no key needed
