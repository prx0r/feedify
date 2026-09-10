"""
L0: Reality Layer - Primary Source Parsers

Parsers for:
- SEC filings (8-K, Form 4, 13D, 13F, XBRL)
- Utility dockets (ERCOT, PJM, FERC)
- Taiwan MOPS monthly revenue
- Physical permits
"""

import json
import urllib.request
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class SECFiling:
    """Parsed SEC filing"""
    form_type: str
    company: str
    cik: str
    filing_date: datetime
    url: str
    items: List[str]  # 8-K items
    exhibits: List[str]
    insider_transactions: List[Dict]  # Form 4
    holdings_changes: List[Dict]  # 13F
    
    @property
    def evidence_score(self) -> float:
        """Score based on form type"""
        scores = {
            "8-K": 0.8,  # Material events
            "4": 0.9,    # Insider transactions
            "SC 13D": 0.95,  # Activist with intent
            "SC 13G": 0.7,   # Passive accumulation
            "13F-HR": 0.6,   # Institutional holdings
            "S-3": 0.3,  # Dilution risk
            "10-Q": 0.5,  # Quarterly updates
            "10-K": 0.4,  # Annual updates
        }
        return scores.get(self.form_type, 0.3)


class SECParser:
    """Parse SEC EDGAR filings"""
    
    BASE_URL = "https://efts.sec.gov/LATEST"
    
    def __init__(self, user_agent: str = "Feedify/1.0"):
        self.user_agent = user_agent
    
    def fetch_recent_filings(self, form_type: str, limit: int = 100) -> List[SECFiling]:
        """Fetch recent filings of a specific type"""
        url = f"{self.BASE_URL}/search-index?q=%22{form_type}%22&dateRange=custom&startdt={datetime.now().strftime('%Y-%m-%d')}&forms={form_type}"
        
        req = urllib.request.Request(url, headers={
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        })
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return self._parse_search_results(data, form_type)
        except Exception as e:
            print(f"SEC fetch error: {e}")
            return []
    
    def _parse_search_results(self, data: dict, form_type: str) -> List[SECFiling]:
        """Parse search results into SECFiling objects"""
        filings = []
        for hit in data.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            filings.append(SECFiling(
                form_type=form_type,
                company=source.get("display_names", ["Unknown"])[0],
                cik=source.get("entity_id", ""),
                filing_date=datetime.fromisoformat(source.get("file_date", "")),
                url=f"https://www.sec.gov/Archives/edgar/data/{source.get('entity_id')}/{source.get('file_num')}",
                items=source.get("items", []),
                exhibits=[],
                insider_transactions=[],
                holdings_changes=[]
            ))
        return filings


class Form4Parser:
    """Parse Form 4 insider transactions"""
    
    @staticmethod
    def parse_transaction(txn: dict) -> Dict:
        """Parse a single Form 4 transaction"""
        return {
            "insider": txn.get("reportingOwner", {}).get("reportingOwnerName", ""),
            "title": txn.get("reportingOwner", {}).get("reportingOwnerTitle", ""),
            "transaction_type": txn.get("nonDerivativeTransaction", {}).get("transactionCoding", {}).get("transactionCode", ""),
            "shares": txn.get("nonDerivativeTransaction", {}).get("transactionAmounts", {}).get("transactionShares", {}).get("value", 0),
            "price": txn.get("nonDerivativeTransaction", {}).get("transactionAmounts", {}).get("transactionPricePerShare", {}).get("value", 0),
            "shares_owned_after": txn.get("nonDerivativeTransaction", {}).get("postTransactionAmounts", {}).get("sharesOwnedFollowingTransaction", {}).get("value", 0),
        }
    
    @staticmethod
    def score_transaction(txn: Dict) -> float:
        """Score a transaction for signal quality"""
        score = 0.0
        
        # Open market purchases are highest signal
        if txn["transaction_type"] == "P":
            score += 0.5
        
        # Large transactions
        value = txn["shares"] * txn["price"]
        if value > 500000:
            score += 0.3
        elif value > 100000:
            score += 0.2
        
        # C-suite titles
        if any(t in txn["title"] for t in ["CEO", "CFO", "COO", "CTO", "President"]):
            score += 0.2
        
        return min(score, 1.0)


class TaiwanMOPSParser:
    """Parse Taiwan MOPS monthly revenue data"""
    
    BASE_URL = "https://mops.twse.com.tw/mops/web/ajax_t21sc04_ifrs"
    
    def fetch_monthly_revenue(self, company_id: str, year: int, month: int) -> Optional[Dict]:
        """Fetch monthly revenue for a company"""
        # Taiwan MOPS requires form submission
        # This is a placeholder for the actual implementation
        return {
            "company_id": company_id,
            "year": year,
            "month": month,
            "revenue": None,
            "yoy_change": None,
            "mom_change": None
        }
    
    def detect_acceleration(self, revenues: List[Dict]) -> bool:
        """Detect revenue acceleration pattern"""
        if len(revenues) < 3:
            return False
        
        # Check for consecutive YoY acceleration
        yoy_changes = [r.get("yoy_change", 0) for r in revenues if r.get("yoy_change") is not None]
        if len(yoy_changes) < 3:
            return False
        
        # Simple acceleration: each month higher than previous
        return all(yoy_changes[i] > yoy_changes[i-1] for i in range(1, len(yoy_changes)))


class ERCOTLargeLoadParser:
    """Parse ERCOT large-load queue"""
    
    def fetch_large_load_queue(self) -> List[Dict]:
        """Fetch current large-load applications"""
        # ERCOT publishes large-load data
        # This is a placeholder for the actual implementation
        return []
    
    def detect_status_transition(self, loads: List[Dict]) -> List[Dict]:
        """Detect status transitions in large-load queue"""
        transitions = []
        for load in loads:
            if load.get("status") == "Study Completed":
                transitions.append({
                    "entity": load.get("entity_name"),
                    "mw": load.get("mw_requested"),
                    "transition": "study_completed",
                    "next_expected": "utility_agreement"
                })
        return transitions


class RealityLayer:
    """Unified L0 Reality Layer"""
    
    def __init__(self):
        self.sec_parser = SECParser()
        self.form4_parser = Form4Parser()
        self.taiwan_parser = TaiwanMOPSParser()
        self.ercot_parser = ERCOTLargeLoadParser()
    
    def scan_all_sources(self) -> List[Dict]:
        """Scan all L0 sources for reality events"""
        events = []
        
        # SEC filings
        for form_type in ["8-K", "4", "SC 13D", "13F-HR"]:
            filings = self.sec_parser.fetch_recent_filings(form_type, limit=50)
            for filing in filings:
                events.append({
                    "source": "sec",
                    "type": form_type,
                    "entity": filing.company,
                    "data": filing.__dict__,
                    "score": filing.evidence_score
                })
        
        # Taiwan MOPS
        # (Would need company IDs to query)
        
        # ERCOT large loads
        large_loads = self.ercot_parser.fetch_large_load_queue()
        for load in large_loads:
            events.append({
                "source": "ercot",
                "type": "large_load",
                "entity": load.get("entity_name"),
                "data": load,
                "score": 0.8
            })
        
        return sorted(events, key=lambda x: x["score"], reverse=True)
