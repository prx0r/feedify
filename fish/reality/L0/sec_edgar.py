"""
SEC EDGAR Adapter - No API key required

Parses:
- 8-K Item 1.01 (contracts)
- Form 4 (insider transactions)
- Schedule 13D/13G (activist/passive)
- 13F-HR (institutional holdings)
- XBRL deltas (financial changes)
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


USER_AGENT = "Feedify/1.0 (research@feedify.ai)"


class SECEdgarAdapter:
    """SEC EDGAR adapter - free, no key required"""
    
    BASE_URL = "https://efts.sec.gov/LATEST"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions"
    
    def __init__(self):
        self.headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    
    def _get(self, url: str) -> Optional[dict]:
        """Make GET request to SEC"""
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"SEC error: {e}")
            return None
    
    def fetch_recent_filings(self, form_type: str, limit: int = 40) -> List[Dict]:
        """Fetch recent filings of a type"""
        url = f"{self.BASE_URL}/search-index?q=%22{form_type}%22&forms={form_type}&dateRange=custom&startdt=2026-08-01&enddt=2026-09-09"
        data = self._get(url)
        if not data:
            return []
        
        filings = []
        for hit in data.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            filings.append({
                "form_type": form_type,
                "company": source.get("display_names", ["Unknown"])[0],
                "cik": source.get("entity_id", ""),
                "filing_date": source.get("file_date", ""),
                "url": f"https://www.sec.gov/Archives/edgar/data/{source.get('entity_id')}/{source.get('file_num')}",
            })
        return filings
    
    def fetch_company_filings(self, cik: str, limit: int = 20) -> List[Dict]:
        """Fetch recent filings for a company"""
        cik_padded = cik.zfill(10)
        url = f"{self.SUBMISSIONS_URL}/CIK{cik_padded}.json"
        data = self._get(url)
        if not data:
            return []
        
        recent = data.get("filings", {}).get("recent", {})
        filings = []
        for i in range(min(limit, len(recent.get("form", [])))):
            filings.append({
                "form_type": recent["form"][i],
                "filing_date": recent["filingDate"][i],
                "accession": recent["accessionNumber"][i],
                "primary_doc": recent["primaryDocument"][i],
            })
        return filings
    
    def parse_form4(self, filing: Dict) -> List[Dict]:
        """Parse Form 4 insider transactions"""
        transactions = []
        # Form 4 XML parsing would go here
        # For now, return structure
        return transactions
    
    def parse_13d(self, filing: Dict) -> Dict:
        """Parse Schedule 13D activist filing"""
        return {
            "filer": filing.get("filer", ""),
            "entity": filing.get("entity", ""),
            "percent_owned": filing.get("percent", 0),
            "purpose": filing.get("purpose", ""),
        }
    
    def to_events(self, filings: List[Dict]) -> List[GenericEvent]:
        """Convert filings to generic events"""
        events = []
        for f in filings:
            event_type_map = {
                "8-K": EventType.ORDER,
                "4": EventType.CASH,  # Insider transaction
                "SC 13D": EventType.QUALIFICATION,  # Activist intent
                "SC 13G": EventType.PIPELINE,  # Passive accumulation
                "13F-HR": EventType.BACKLOG,  # Institutional holdings
            }
            
            event = GenericEvent(
                event_id=GenericEvent.generate_id("sec_edgar", f.get("accession", f.get("url", ""))),
                source="sec_edgar",
                source_record_id=f.get("accession", f.get("url", "")),
                observed_at=datetime.now(),
                effective_at=datetime.fromisoformat(f["filing_date"]) if f.get("filing_date") else datetime.now(),
                entity_ids=[f.get("cik", f.get("company", ""))],
                event_type=event_type_map.get(f["form_type"], EventType.IDEA),
                evidence=[Evidence(url=f.get("url", ""))],
                confidence=0.8,
            )
            events.append(event)
        
        return events


# Human task: No SEC EDGAR API key needed (free), but need to register
# for full-text search API. Use basic search for now.
