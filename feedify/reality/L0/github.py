"""
GitHub Capability Detection Adapter
Uses GitHub API for repo/release/contributor tracking
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class GitHubAdapter:
    """GitHub API adapter"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str = ""):
        self.token = token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    def _get(self, url: str) -> Optional[dict]:
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"GitHub error: {e}")
            return None
    
    def fetch_recent_releases(self, org: str, limit: int = 10) -> List[Dict]:
        """Fetch recent releases for an org"""
        url = f"{self.BASE_URL}/orgs/{org}/repos?sort=updated&per_page={limit}"
        data = self._get(url)
        if not data:
            return []
        return data
    
    def fetch_releases(self, owner: str, repo: str, limit: int = 10) -> List[Dict]:
        """Fetch releases for a repo"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/releases?per_page={limit}"
        data = self._get(url)
        if not data:
            return []
        return data
    
    def fetch_contributors(self, owner: str, repo: str) -> List[Dict]:
        """Fetch contributors"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contributors"
        data = self._get(url)
        if not data:
            return []
        return data
    
    def detect_capability_creation(self, repos: List[Dict]) -> List[Dict]:
        """Detect when repos indicate new capability"""
        capabilities = []
        for r in repos:
            if r.get("stargazers_count", 0) > 1000:
                capabilities.append({
                    "repo": r["full_name"],
                    "stars": r["stargazers_count"],
                    "language": r.get("language", ""),
                    "description": r.get("description", ""),
                })
        return capabilities
    
    def to_events(self, repos: List[Dict]) -> List[GenericEvent]:
        events = []
        for r in repos:
            event = GenericEvent(
                event_id=GenericEvent.generate_id("github", r.get("full_name", "")),
                source="github",
                source_record_id=r.get("full_name", ""),
                observed_at=datetime.now(),
                effective_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") else datetime.now(),
                entity_ids=[r.get("full_name", "")],
                event_type=EventType.PAPER,
                evidence=[Evidence(url=r.get("html_url", ""))],
                confidence=0.7,
            )
            events.append(event)
        return events


# Human task: GitHub token available in agent-vault
