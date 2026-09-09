"""
HuggingFace Hub Adapter - Model/dataset capability diffusion
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class HuggingFaceAdapter:
    """HuggingFace Hub API - free"""
    
    BASE_URL = "https://huggingface.co/api"
    
    def search_models(self, query: str, limit: int = 10) -> List[Dict]:
        """Search models"""
        import urllib.parse
        params = urllib.parse.urlencode({"search": query, "limit": limit})
        url = f"{self.BASE_URL}/models?{params}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"HuggingFace error: {e}")
            return []
    
    def get_model_downloads(self, model_id: str) -> int:
        """Get download count"""
        url = f"{self.BASE_URL}/models/{model_id}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("downloads", 0)
        except:
            return 0
    
    def detect_capability_diffusion(self, models: List[Dict]) -> List[Dict]:
        """Detect when capabilities become accessible"""
        accessible = []
        for m in models:
            if m.get("downloads", 0) > 10000:
                accessible.append({
                    "model": m.get("id", ""),
                    "downloads": m.get("downloads", 0),
                    "pipeline_tag": m.get("pipeline_tag", ""),
                })
        return accessible
    
    def to_events(self, models: List[Dict]) -> List[GenericEvent]:
        events = []
        for m in models:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("huggingface", m.get("id", "")),
                source="huggingface",
                source_record_id=m.get("id", ""),
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[m.get("id", "")],
                event_type=EventType.PAPER,
                evidence=[Evidence(url=f"https://huggingface.co/{m.get('id', '')}")],
                confidence=0.6,
            )
            events.append(event)
        return events


# Human task: HuggingFace is free, no key needed
