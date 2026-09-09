"""
Reality Feed Adapter Registry
Wires all adapters together
"""

from datetime import datetime
from typing import List, Dict
from .event_store import EventStore, GenericEvent
from .L0.sec_edgar import SECEdgarAdapter
from .L0.twse import TWSEAdapter
from .L0.usaspending import USAspendingAdapter
from .L0.github import GitHubAdapter
from .L0.gleif import GLEIFAdapter
from .L0.ercot import ERCOTAdapter
from .L0.pudl import PUDLAdapter
from .L0.ferc import FERCAdapter
from .L0.sam import SAMGovAdapter
from .L0.nrc_adams import NRCADAMSAdapter
from .L1.openalex import OpenAlexAdapter, ArXivAdapter
from .L1.huggingface import HuggingFaceAdapter
from .L1.patent import PatentAdapter
from .L1.jobs import JobBoardAdapter


class RealityRegistry:
    """Registry of all Reality Feed adapters"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.store = EventStore()
        
        # Initialize adapters
        self.adapters = {
            "sec_edgar": SECEdgarAdapter(),
            "twse": TWSEAdapter(),
            "usaspending": USAspendingAdapter(),
            "github": GitHubAdapter(token=self.config.get("github_token", "")),
            "gleif": GLEIFAdapter(),
            "ercot": ERCOTAdapter(),
            "pudl": PUDLAdapter(),
            "ferc": FERCAdapter(),
            "sam": SAMGovAdapter(api_key=self.config.get("sam_api_key", "")),
            "nrc_adams": NRCADAMSAdapter(api_key=self.config.get("nrc_api_key", "")),
            "openalex": OpenAlexAdapter(email=self.config.get("openalex_email", "")),
            "arxiv": ArXivAdapter(),
            "huggingface": HuggingFaceAdapter(),
            "patent": PatentAdapter(),
            "jobs": JobBoardAdapter(),
        }
    
    def scan_all(self) -> List[GenericEvent]:
        """Scan all adapters and return events"""
        all_events = []
        
        # L0 - Reality
        print("Scanning SEC EDGAR...")
        filings = self.adapters["sec_edgar"].fetch_recent_filings("8-K", limit=10)
        all_events.extend(self.adapters["sec_edgar"].to_events(filings))
        
        print("Scanning TWSE...")
        revenue = self.adapters["twse"].fetch_monthly_revenue()
        all_events.extend(self.adapters["twse"].to_events(revenue))
        
        print("Scanning USAspending...")
        awards = self.adapters["usaspending"].search_awards(["semiconductor", "nuclear", "HALEU"])
        all_events.extend(self.adapters["usaspending"].to_events(awards))
        
        print("Scanning GLEIF...")
        # GLEIF is for entity resolution, not scanning
        
        # L1 - Technical Frontier
        print("Scanning OpenAlex...")
        works = self.adapters["openalex"].search_works("glass interposer advanced packaging")
        all_events.extend(self.adapters["openalex"].to_events(works))
        
        print("Scanning arXiv...")
        papers = self.adapters["arxiv"].search("cat:cs.AR AND glass packaging")
        # arXiv returns XML, convert to events
        
        print("Scanning HuggingFace...")
        models = self.adapters["huggingface"].search_models("inference optimization")
        all_events.extend(self.adapters["huggingface"].to_events(models))
        
        print("Scanning GitHub...")
        repos = self.adapters["github"].fetch_recent_releases("pytorch", limit=5)
        all_events.extend(self.adapters["github"].to_events(repos))
        
        # Store events
        for event in all_events:
            self.store.append(event)
        
        print(f"\nTotal events: {len(all_events)}")
        return all_events
    
    def get_stats(self) -> Dict:
        """Get statistics about scanned events"""
        events = self.store.query(limit=10000)
        
        by_source = {}
        by_type = {}
        for e in events:
            src = e["source"]
            typ = e["event_type"]
            by_source[src] = by_source.get(src, 0) + 1
            by_type[typ] = by_type.get(typ, 0) + 1
        
        return {
            "total_events": len(events),
            "by_source": by_source,
            "by_type": by_type,
        }
