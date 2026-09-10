"""
OpenAlex + arXiv Research Graph Adapter
CC0 research graph, $1/day free API
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class OpenAlexAdapter:
    """OpenAlex API - free tier"""
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self, email: str = ""):
        self.email = email
        self.headers = {"Accept": "application/json"}
    
    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        import urllib.parse
        url = f"{self.BASE_URL}/{endpoint}"
        query_params = {}
        if self.email:
            query_params["mailto"] = self.email
        if params:
            query_params.update(params)
        
        if query_params:
            url += "?" + urllib.parse.urlencode(query_params)
        
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"OpenAlex error: {e}")
            return None
    
    def search_works(self, query: str, limit: int = 25) -> List[Dict]:
        """Search academic works"""
        data = self._get("works", {"search": query, "per_page": limit})
        if not data:
            return []
        return data.get("results", [])
    
    def get_topic_trend(self, topic: str) -> Dict:
        """Get publication trend for a topic"""
        data = self._get("works", {"search": topic, "group_by": "publication_year"})
        if not data:
            return {}
        
        groups = data.get("group_by", [])
        trend = {}
        for g in groups:
            year = g.get("key", "")
            count = g.get("count", 0)
            trend[year] = count
        
        return trend
    
    def to_events(self, works: List[Dict]) -> List[GenericEvent]:
        events = []
        for w in works:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("openalex", w.get("id", "")),
                source="openalex",
                source_record_id=w.get("id", ""),
                observed_at=datetime.now(),
                effective_at=datetime.fromisoformat(w["publication_date"]) if w.get("publication_date") else datetime.now(),
                entity_ids=[a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:3]],
                technology_ids=[t.get("display_name", "") for t in w.get("topics", [])[:3]],
                event_type=EventType.PAPER,
                evidence=[Evidence(url=w.get("doi", w.get("id", "")))],
                confidence=0.6,
            )
            events.append(event)
        return events


class ArXivAdapter:
    """arXiv API - free"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search arXiv"""
        import urllib.parse
        params = urllib.parse.urlencode({"search_query": query, "max_results": limit})
        url = f"{self.BASE_URL}?{params}"
        
        req = urllib.request.Request(url, headers={"Accept": "application/xml"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                # Parse XML
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.read())
                entries = root.findall("{http://www.w3.org/2005/Atom}entry")
                return [{"title": e.find("{http://www.w3.org/2005/Atom}title").text,
                         "id": e.find("{http://www.w3.org/2005/Atom}id").text,
                         "published": e.find("{http://www.w3.org/2005/Atom}published").text}
                        for e in entries]
        except Exception as e:
            print(f"arXiv error: {e}")
            return []


# Human task: OpenAlex free tier works, arXiv is free
