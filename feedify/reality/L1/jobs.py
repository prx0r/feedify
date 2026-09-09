"""
Job Board Adapter - Greenhouse/Ashby/Lever
Detects hiring intent before production ramps
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class GreenhouseAdapter:
    """Greenhouse job board - free public GET"""
    
    def fetch_jobs(self, board: str) -> List[Dict]:
        """Fetch jobs from Greenhouse board"""
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("jobs", [])
        except Exception as e:
            print(f"Greenhouse error: {e}")
            return []
    
    def detect_hiring_shift(self, jobs: List[Dict]) -> Dict:
        """Detect semantic change in hiring"""
        departments = {}
        for j in jobs:
            dept = j.get("departments", [{}])[0].get("name", "Unknown") if j.get("departments") else "Unknown"
            departments[dept] = departments.get(dept, 0) + 1
        
        return departments


class AshbyAdapter:
    """Ashby job board - free public"""
    
    def fetch_jobs(self, board: str) -> List[Dict]:
        url = f"https://jobs.ashbyhq.com/api/posting-api/job-board/{board}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("jobPostings", [])
        except Exception as e:
            print(f"Ashby error: {e}")
            return []


class LeverAdapter:
    """Lever job board - free public"""
    
    def fetch_jobs(self, company: str) -> List[Dict]:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"Lever error: {e}")
            return []


class JobBoardAdapter:
    """Unified job board adapter"""
    
    def __init__(self):
        self.greenhouse = GreenhouseAdapter()
        self.ashby = AshbyAdapter()
        self.lever = LeverAdapter()
    
    def fetch_all_jobs(self, company: str) -> List[Dict]:
        """Fetch jobs from all platforms"""
        jobs = []
        jobs.extend(self.greenhouse.fetch_jobs(company))
        jobs.extend(self.ashby.fetch_jobs(company))
        jobs.extend(self.lever.fetch_jobs(company))
        return jobs
    
    def to_events(self, jobs: List[Dict]) -> List[GenericEvent]:
        events = []
        for j in jobs:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("jobs", j.get("id", j.get("uuid", ""))),
                source="jobs",
                source_record_id=j.get("id", j.get("uuid", "")),
                observed_at=datetime.now(),
                effective_at=datetime.now(),
                entity_ids=[j.get("company", j.get("companyName", ""))],
                event_type=EventType.HIRING,  # Will add to enum
                evidence=[Evidence(url=j.get("absolute_url", j.get("url", "")))],
                confidence=0.7,
            )
            events.append(event)
        return events


# Human task: All three are free, no keys needed
