"""
L2: Institutional Intent Layer - Government Procurement Graph

Tracks:
- SAM.gov opportunities and awards
- USAspending federal awards
- SBIR/STTR grants
- DARPA BAAs
- DOE HALEU allocations
- CHIPS Act awards
"""

import json
import urllib.request
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class GovernmentAward:
    """A government contract or grant"""
    award_id: str
    agency: str
    recipient: str
    description: str
    amount: float
    award_date: datetime
    award_type: str  # "contract", "grant", "sbir", "chips"
    url: str
    
    @property
    def evidence_score(self) -> float:
        """Score based on award type"""
        scores = {
            "chips": 0.95,  # CHIPS Act awards - direct semiconductor
            "haleu": 0.95,  # Nuclear fuel - direct to LEU
            "sbir_phase2": 0.8,  # SBIR Phase II - validated technology
            "sbir_phase1": 0.5,  # SBIR Phase I - early stage
            "darpa": 0.9,   # DARPA - cutting edge
            "contract": 0.7,  # Regular contract
            "grant": 0.6,    # Research grant
        }
        return scores.get(self.award_type, 0.4)


class SAMGovParser:
    """Parse SAM.gov opportunities and awards"""
    
    BASE_URL = "https://api.sam.gov"
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
    
    def search_opportunities(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        """Search for opportunities by keywords"""
        # SAM.gov API requires registration
        # This is a placeholder for actual implementation
        return []
    
    def search_awards(self, keywords: List[str], limit: int = 50) -> List[GovernmentAward]:
        """Search for contract awards"""
        # Would use SAM.gov Awards API
        return []


class USAspendingParser:
    """Parse USAspending federal awards"""
    
    BASE_URL = "https://api.usaspending.gov"
    
    def search_awards(self, keywords: List[str], limit: int = 50) -> List[GovernmentAward]:
        """Search for federal awards"""
        url = f"{self.BASE_URL}/api/v2/search/spending_by_award/"
        
        payload = {
            "filters": {
                "keywords": keywords,
                "time_period": [{"start_date": "2024-01-01", "end_date": "2026-12-31"}]
            },
            "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", "Description"],
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
                return self._parse_awards(data.get("results", []))
        except Exception as e:
            print(f"USAspending error: {e}")
            return []
    
    def _parse_awards(self, results: List[Dict]) -> List[GovernmentAward]:
        """Parse award results"""
        awards = []
        for r in results:
            awards.append(GovernmentAward(
                award_id=r.get("Award ID", ""),
                agency=r.get("Awarding Agency", ""),
                recipient=r.get("Recipient Name", ""),
                description=r.get("Description", ""),
                amount=r.get("Award Amount", 0),
                award_date=datetime.now(),  # Would parse from data
                award_type="contract",
                url=f"https://www.usaspending.gov/award/{r.get('Award ID', '')}"
            ))
        return awards


class CHIPSActParser:
    """Parse CHIPS Act awards and LOIs"""
    
    # Known CHIPS Act recipients
    KNOWN_AWARDS = [
        {"recipient": "TSMC", "amount": 6600000000, "status": "finalized"},
        {"recipient": "Samsung", "amount": 6400000000, "status": "finalized"},
        {"recipient": "Intel", "amount": 8500000000, "status": "finalized"},
        {"recipient": "Micron", "amount": 6100000000, "status": "finalized"},
        {"recipient": "SK Hynix", "amount": 4500000000, "status": "finalized"},
        {"recipient": "GlobalFoundries", "amount": 1500000000, "status": "finalized"},
        {"recipient": "Aeluma", "amount": 30000000, "status": "loi"},
    ]
    
    def get_recent_awards(self) -> List[GovernmentAward]:
        """Get recent CHIPS Act awards"""
        awards = []
        for a in self.KNOWN_AWARDS:
            awards.append(GovernmentAward(
                award_id=f"CHIPS-{a['recipient']}",
                agency="NIST/CHIPS",
                recipient=a["recipient"],
                description=f"CHIPS Act award to {a['recipient']}",
                amount=a["amount"],
                award_date=datetime.now(),
                award_type="chips",
                url="https://www.nist.gov/chips"
            ))
        return awards


class HALEUAllocator:
    """Track HALEU fuel allocations"""
    
    KNOWN_ALLOCATIONS = [
        {"recipient": "Centrus Energy", "amount": 900000000, "type": "enrichment"},
        {"recipient": "X-energy", "amount": None, "type": "fuel"},
        {"recipient": "Kairos Power", "amount": None, "type": "fuel"},
        {"recipient": "TerraPower", "amount": None, "type": "fuel"},
    ]
    
    def get_allocations(self) -> List[GovernmentAward]:
        """Get HALEU allocations"""
        awards = []
        for a in self.KNOWN_ALLOCATIONS:
            if a["amount"]:
                awards.append(GovernmentAward(
                    award_id=f"HALEU-{a['recipient']}",
                    agency="DOE",
                    recipient=a["recipient"],
                    description=f"HALEU {a['type']} allocation",
                    amount=a["amount"],
                    award_date=datetime.now(),
                    award_type="haleu",
                    url="https://www.energy.gov/ne/haleu-enrichment-services"
                ))
        return awards


class InstitutionalLayer:
    """Unified L2 Institutional Intent Layer"""
    
    def __init__(self):
        self.sam_parser = SAMGovParser()
        self.usaspending_parser = USAspendingParser()
        self.chips_parser = CHIPSActParser()
        self.haleu_allocator = HALEUAllocator()
    
    def scan_all_sources(self) -> List[GovernmentAward]:
        """Scan all L2 sources for institutional intent"""
        awards = []
        
        # CHIPS Act awards
        awards.extend(self.chips_parser.get_recent_awards())
        
        # HALEU allocations
        awards.extend(self.haleu_allocator.get_allocations())
        
        # USAspending
        semiconductor_keywords = ["semiconductor", "chip", "packaging", "photonics", "nuclear", "HALEU"]
        usaspending = self.usaspending_parser.search_awards(semiconductor_keywords)
        awards.extend(usaspending)
        
        return sorted(awards, key=lambda x: x.evidence_score, reverse=True)
    
    def detect_bottleneck_convergence(self) -> List[Dict]:
        """Detect when multiple sources converge on same bottleneck"""
        awards = self.scan_all_sources()
        
        # Group by recipient
        by_recipient = {}
        for a in awards:
            if a.recipient not in by_recipient:
                by_recipient[a.recipient] = []
            by_recipient[a.recipient].append(a)
        
        # Find convergences
        convergences = []
        for recipient, recipient_awards in by_recipient.items():
            if len(recipient_awards) > 1:
                convergences.append({
                    "recipient": recipient,
                    "award_count": len(recipient_awards),
                    "total_amount": sum(a.amount for a in recipient_awards if a.amount),
                    "sources": list(set(a.agency for a in recipient_awards)),
                    "score": sum(a.evidence_score for a in recipient_awards)
                })
        
        return sorted(convergences, key=lambda x: x["score"], reverse=True)
