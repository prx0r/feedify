from __future__ import annotations

from feedify.schemas import NormalizedItem
from feedify.settings import get_settings

from .base import SourceAdapter
from .utils import parse_datetime


class StoreLeadsAdapter(SourceAdapter):
    name = "storeleads"
    base_url = "https://storeleads.app/json/api/v1/all/app"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = get_settings().storeleads_api_key

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        if not self.configured:
            return []
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.client.get(
            self.base_url,
            headers=headers,
            params={
                "page_size": min(limit, 50),
                "f:p": "shopify",
                "sort": "-created_at,-installs",
                "fields": "name,token,platform,description,app_store_url,vendor_name,vendor_website,created_at,installs,installs_30d,installs_90d,review_count,categories,plans",
            },
        )
        response.raise_for_status()
        rows = response.json().get("apps", [])
        return [
            NormalizedItem(
                source_type=self.name,
                external_id=f"{row.get('platform','shopify')}.{row.get('token') or row.get('name')}",
                title=row.get("name") or row.get("token") or "Unknown app",
                url=row.get("app_store_url") or row.get("vendor_website"),
                body=row.get("description"),
                author=row.get("vendor_name"),
                published_at=parse_datetime(row.get("created_at")),
                metrics={
                    "installs": row.get("installs") or 0,
                    "installs_30d": row.get("installs_30d") or 0,
                    "installs_90d": row.get("installs_90d") or 0,
                    "review_count": row.get("review_count") or 0,
                    "categories": row.get("categories") or [],
                    "plans": row.get("plans") or [],
                },
                raw=row,
            )
            for row in rows
        ]
