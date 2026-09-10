"""
Korea OpenDART Adapter

Free key from FSS.
Disclosures, XBRL, capital increases, treasury shares.
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class OpenDARTAdapter:
    """Korea OpenDART adapter - free key required"""
    
    BASE_URL = "https://opendart.fss.or.kr/api"
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
    
    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        if not self.api_key:
            print("OpenDART: No API key configured")
            return None
        
        url = f"{self.BASE_URL}/{endpoint}?crtfc_key={self.api_key}"
        if params:
            url += "&" + "&".join(f"{k}={v}" for k, v in params.items())
        
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"OpenDART error: {e}")
            return None
    
    def search_disclosures(self, corp_code: str, date_range: str = "20260801~20260909") -> List[Dict]:
        """Search company disclosures"""
        data = self._get("list.json", {"corp_code": corp_code, "bgn_de": date_range[:8], "end_de": date_range[9:]})
        if not data:
            return []
        return data.get("list", [])
    
    def get_company_info(self, corp_code: str) -> Optional[Dict]:
        """Get company basic information"""
        return self._get("company.json", {"corp_code": corp_code})
    
    def get_capital_increase(self, corp_code: str) -> List[Dict]:
        """Get paid-in capital increases"""
        data = self._get("stock.json", {"corp_code": corp_code, "pblntf_ty_code": "005"})
        if not data:
            return []
        return data.get("list", [])
    
    def to_events(self, disclosures: List[Dict]) -> List[GenericEvent]:
        """Convert to generic events"""
        events = []
        for d in disclosures:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("opendart", d.get("rcept_no", "")),
                source="opendart",
                source_record_id=d.get("rcept_no", ""),
                observed_at=datetime.now(),
                effective_at=datetime.strptime(d.get("rcept_dt", ""), "%Y%m%d") if d.get("rcept_dt") else datetime.now(),
                entity_ids=[d.get("corp_code", "")],
                event_type=EventType.IDEA,
                evidence=[Evidence(url=f"https://opendart.fss.or.kr/disclosure/{d.get('rcept_no', '')}")],
                confidence=0.7,
            )
            events.append(event)
        return events


# Human task: Need OpenDART API key from https://opendart.fss.or.kr
