from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from feedify.schemas import NormalizedItem
from feedify.settings import get_settings

from .base import SourceAdapter
from .utils import parse_datetime


class XAdapter(SourceAdapter):
    """X/Twitter intelligence via GetXAPI — the main Feedify engine.

    Follows BEAR budget discipline: balance check is free, reads are
    ~$0.001/call, watchlist-bounded with small per-handle counts, and
    every call is logged. Raw tweet JSON is preserved verbatim
    (BEAR Rule 1: filter during analysis, never during ingestion) and
    author_id is the stable author key (BEAR Rule 4: usernames change).
    """

    name = "x"
    base_url = "https://api.getxapi.com"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings = get_settings()
        self.primary_key = settings.getxapi_key
        self.backup_key = settings.getxapi_backup_key
        self._active_key = settings.getxapi_key
        self._using_backup = False
        self.calls_made = 0

    @property
    def configured(self) -> bool:
        return bool(self.primary_key or self.backup_key)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._active_key}"}

    async def _get(self, path: str, params: dict | None = None) -> dict:
        response = await self.client.get(
            f"{self.base_url}{path}", headers=self._headers(), params=params or {}
        )
        response.raise_for_status()
        self.calls_made += 1
        return response.json()

    async def balance(self) -> float:
        """Free account check. Falls back to backup key when primary is dry."""
        for key in (self.primary_key, self.backup_key):
            if not key:
                continue
            self._active_key = key
            try:
                data = await self._get("/account/me")
                balance = float(data.get("credits_remaining",
                                         data.get("balance_total", 0)) or 0)
                self._using_backup = (key == self.backup_key)
                return balance
            except Exception:
                continue
        return 0.0

    def watchlist(self) -> list[dict]:
        settings = get_settings()
        try:
            data = json.loads(Path(settings.getxapi_watchlist_path).read_text())
            if isinstance(data, list):
                return data[: settings.getxapi_max_handles]
        except (OSError, json.JSONDecodeError):
            pass
        return []

    async def fetch_handle(self, handle: str, count: int = 3) -> list[dict]:
        """Recent posts via advanced search. One $0.001 call per handle."""
        data = await self._get(
            "/twitter/tweet/advanced_search",
            {"q": f"from:{handle}", "product": "Latest", "count": count},
        )
        return data.get("tweets", [])

    def normalize(self, tweet: dict) -> NormalizedItem | None:
        tweet_id = str(tweet.get("id") or "")
        if not tweet_id:
            return None
        author = tweet.get("author") or {}
        author_id = str(author.get("id") or author.get("userName") or "unknown")
        text = tweet.get("text") or ""
        return NormalizedItem(
            source_type=self.name,
            external_id=tweet_id,
            title=text[:160],
            url=tweet.get("url") or tweet.get("twitterUrl"),
            body=text,
            author=author_id,
            published_at=parse_datetime(tweet.get("createdAt")),
            metrics={
                "author_handle": author.get("userName"),
                "author_name": author.get("name"),
                "author_followers": author.get("followers"),
                "author_verified": bool(author.get("isVerified")),
                "likes": tweet.get("likeCount") or 0,
                "views": tweet.get("viewCount") or 0,
                "reposts": tweet.get("retweetCount") or 0,
                "replies": tweet.get("replyCount") or 0,
                "quotes": tweet.get("quoteCount") or 0,
                "bookmarks": tweet.get("bookmarkCount") or 0,
                "lang": tweet.get("lang"),
                "is_reply": bool(tweet.get("isReply")),
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            raw=tweet,
        )

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        settings = get_settings()
        if await self.balance() <= 0:
            return []
        items: list[NormalizedItem] = []
        per_handle = max(1, settings.getxapi_per_handle_count)
        for entry in self.watchlist():
            handle = entry.get("handle") if isinstance(entry, dict) else entry
            if not handle or len(items) >= limit:
                break
            try:
                for tweet in await self.fetch_handle(str(handle), per_handle):
                    item = self.normalize(tweet)
                    if item is not None:
                        items.append(item)
                    if len(items) >= limit:
                        break
            except Exception:
                continue
        return items
