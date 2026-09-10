from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fish.schemas import NormalizedItem
from fish.settings import get_settings

from .base import SourceAdapter
from .utils import parse_datetime


class GitHubAdapter(SourceAdapter):
    name = "github"
    base_url = "https://api.github.com"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = get_settings().github_token

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        since = (datetime.now(timezone.utc) - timedelta(days=21)).date().isoformat()
        q = f"created:>{since} stars:>15"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "feedify-alpha/0.1"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = await self.client.get(
            f"{self.base_url}/search/repositories",
            headers=headers,
            params={"q": q, "sort": "stars", "order": "desc", "per_page": min(limit, 100)},
        )
        response.raise_for_status()
        rows = response.json().get("items", [])
        return [
            NormalizedItem(
                source_type=self.name,
                external_id=row["full_name"],
                title=row["full_name"],
                url=row.get("html_url"),
                body=row.get("description"),
                author=(row.get("owner") or {}).get("login"),
                published_at=parse_datetime(row.get("created_at")),
                metrics={
                    "stars": row.get("stargazers_count") or 0,
                    "forks": row.get("forks_count") or 0,
                    "watchers": row.get("watchers_count") or 0,
                    "open_issues": row.get("open_issues_count") or 0,
                    "language": row.get("language"),
                    "topics": row.get("topics") or [],
                    "pushed_at": row.get("pushed_at"),
                },
                raw=row,
            )
            for row in rows
        ]
