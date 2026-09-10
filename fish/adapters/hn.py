from __future__ import annotations

from datetime import datetime, timezone

from fish.schemas import NormalizedItem

from .base import SourceAdapter


class HackerNewsAdapter(SourceAdapter):
    name = "hackernews"
    base_url = "https://hacker-news.firebaseio.com/v0"

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        ids_response = await self.client.get(f"{self.base_url}/newstories.json")
        ids_response.raise_for_status()
        ids = ids_response.json()[: max(limit * 3, limit)]
        out: list[NormalizedItem] = []
        for item_id in ids:
            if len(out) >= limit:
                break
            response = await self.client.get(f"{self.base_url}/item/{item_id}.json")
            if response.status_code != 200:
                continue
            row = response.json() or {}
            title = row.get("title") or ""
            text = row.get("text") or ""
            # Bias toward launches and primitives, not general discussion.
            is_builder = title.lower().startswith("show hn:") or any(
                k in (title + " " + text).lower()
                for k in ("mcp", "api", "agent", "open source", "sdk", "marketplace", "search", "commerce")
            )
            if not is_builder:
                continue
            ts = row.get("time")
            published = datetime.fromtimestamp(ts, timezone.utc) if ts else None
            out.append(
                NormalizedItem(
                    source_type=self.name,
                    external_id=str(item_id),
                    title=title,
                    url=row.get("url") or f"https://news.ycombinator.com/item?id={item_id}",
                    body=text,
                    author=row.get("by"),
                    published_at=published,
                    metrics={"score": row.get("score") or 0, "comments": row.get("descendants") or 0},
                    raw=row,
                )
            )
        return out
