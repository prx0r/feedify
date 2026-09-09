"""
TWSE OpenAPI Adapter - Monthly revenue, insiders

Free official OpenAPI for Taiwan companies.
Key endpoint: /opendata/t187ap05_L (monthly revenue)
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class TWSEAdapter:
    """Taiwan Stock Exchange adapter - free, no key"""
    
    BASE_URL = "https://openapi.twse.com.tw"
    
    def __init__(self):
        self.headers = {"User-Agent": "Feedify/1.0", "Accept": "application/json"}
    
    def _get(self, url: str) -> Optional[dict]:
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"TWSE error: {e}")
            return None
    
    def fetch_monthly_revenue(self, month: str = "202608") -> List[Dict]:
        """Fetch monthly revenue summary for all listed companies"""
        url = f"{self.BASE_URL}/opendata/t187ap05_L"
        data = self._get(url)
        if not data:
            return []
        return data.get("data", [])
    
    def fetch_company_revenue(self, company_id: str) -> List[Dict]:
        """Fetch revenue for specific company"""
        all_revenue = self.fetch_monthly_revenue()
        return [r for r in all_revenue if r.get("公司代號") == company_id]
    
    def detect_acceleration(self, revenues: List[Dict]) -> bool:
        """Detect YoY revenue acceleration"""
        yoy = [float(r.get("與去年同月增減%", "0").replace(",", "")) for r in revenues if r.get("與去年同月增減%")]
        if len(yoy) < 3:
            return False
        return all(yoy[i] > yoy[i-1] for i in range(1, len(yoy)))
    
    def to_events(self, revenues: List[Dict]) -> List[GenericEvent]:
        """Convert to generic events"""
        events = []
        for r in revenues:
            yoy_str = r.get("與去年同月增減%", "0").replace(",", "")
            try:
                yoy = float(yoy_str)
            except:
                yoy = 0
            
            event = GenericEvent(
                event_id=GenericEvent.generate_id("twse", f"{r.get('公司代號', '')}_{r.get('月份', '')}"),
                source="twse",
                source_record_id=f"{r.get('公司代號', '')}_{r.get('月份', '')}",
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[r.get("公司代號", "")],
                event_type=EventType.REVENUE,
                quantity=yoy,
                unit="percent_yoy",
                evidence=[Evidence(url="https://openapi.twse.com.tw")],
                confidence=0.9,
                economic_materiality=abs(yoy) / 100,
            )
            events.append(event)
        return events


class TaiwanMOPSAdapter:
    """Taiwan MOPS for detailed financials"""
    
    def fetch_monthly_revenue(self, company_id: str, year: int, month: int) -> Optional[Dict]:
        """Fetch detailed monthly revenue"""
        # MOPS requires form submission
        return None  # Placeholder


# Human task: TWSE OpenAPI is free, no key needed
# Taiwan MOPS needs form submission (more complex)
