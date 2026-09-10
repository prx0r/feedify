from __future__ import annotations

from fish.schemas import NormalizedItem

from .base import SourceAdapter
from .utils import parse_datetime


class GlamaAdapter(SourceAdapter):
    name = "glama"
    base_url = "https://glama.ai/api/mcp/v1/servers"

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        # Glama's directory API is public. Its response shape has changed over time,
        # so normalize both a bare list and common {servers|data|items} envelopes.
        response = await self.client.get(self.base_url, params={"limit": limit})
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            rows = payload
        else:
            rows = payload.get("servers") or payload.get("data") or payload.get("items") or []
        out: list[NormalizedItem] = []
        for row in rows[:limit]:
            owner = row.get("owner") or row.get("namespace") or row.get("author") or "unknown"
            repo = row.get("slug") or row.get("name") or row.get("id")
            external_id = f"{owner}/{repo}"
            attrs = row.get("attributes") or {}
            categories = row.get("categories") or attrs.get("categories") or []
            out.append(
                NormalizedItem(
                    source_type=self.name,
                    external_id=str(external_id),
                    title=row.get("name") or str(repo),
                    url=row.get("url") or row.get("homepage") or f"https://glama.ai/mcp/servers/{external_id}",
                    body=row.get("description") or row.get("summary"),
                    author=str(owner),
                    published_at=parse_datetime(row.get("createdAt") or row.get("created_at")),
                    metrics={
                        "stars": row.get("stars") or attrs.get("stars") or 0,
                        "weekly_downloads": row.get("weeklyDownloads") or attrs.get("weekly_downloads") or 0,
                        "recent_stars": row.get("recentStars") or attrs.get("recent_stars") or 0,
                        "categories": categories,
                        "official": bool(row.get("official") or attrs.get("official")),
                        "updated_at": row.get("updatedAt") or row.get("updated_at"),
                    },
                    raw=row,
                )
            )
        return out
