"""
GLEIF Entity Resolver - Global Legal Entity Identifier
Free, no registration
"""

import json
import urllib.request
from typing import List, Dict, Optional


class GLEIFAdapter:
    """GLEIF API - free, no key"""
    
    BASE_URL = "https://api.gleif.org/api/v1"
    
    def _get(self, endpoint: str) -> Optional[dict]:
        url = f"{self.BASE_URL}/{endpoint}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.api+json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"GLEIF error: {e}")
            return None
    
    def lookup_lei(self, lei: str) -> Optional[Dict]:
        """Look up entity by LEI"""
        data = self._get(f"lei-records/{lei}")
        if not data:
            return None
        records = data.get("data", {}).get("attributes", {})
        return {
            "lei": lei,
            "name": records.get("entity", {}).get("legalName", {}).get("name", ""),
            "country": records.get("entity", {}).get("registeredIn", ""),
            "status": records.get("entity", {}).get("status", ""),
        }
    
    def search_entity(self, name: str) -> List[Dict]:
        """Search entity by name"""
        import urllib.parse
        params = urllib.parse.urlencode({"filter[entity.legalName]": name})
        data = self._get(f"lei-records?{params}")
        if not data:
            return []
        
        return [{
            "lei": r.get("id", ""),
            "name": r.get("attributes", {}).get("entity", {}).get("legalName", {}).get("name", ""),
            "country": r.get("attributes", {}).get("entity", {}).get("registeredIn", ""),
        } for r in data.get("data", [])]


# Human task: GLEIF is free, no key needed
