from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fish.schemas import NormalizedItem
from fish.settings import get_settings

from .base import SourceAdapter


class AppfiguresAdapter(SourceAdapter):
    """Estimate ingestion for configured app IDs.

    Appfigures' estimates route requires licensed product IDs. Keep the IDs in
    APPFIGURES_PRODUCT_IDS as a comma-separated env var if you want this source enabled.
    """

    name = "appfigures"
    base_url = "https://api.appfigures.com/v2"

    def __init__(self, *args, **kwargs):
        import os

        super().__init__(*args, **kwargs)
        settings = get_settings()
        self.username = settings.appfigures_username
        self.password = settings.appfigures_password
        self.client_key = settings.appfigures_client_key
        self.product_ids = [x.strip() for x in os.getenv("APPFIGURES_PRODUCT_IDS", "").split(",") if x.strip()]

    @property
    def configured(self) -> bool:
        return bool(self.username and self.password and self.client_key and self.product_ids)

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        if not self.configured:
            return []
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=30)
        headers = {"X-Client-Key": self.client_key}
        response = await self.client.get(
            f"{self.base_url}/reports/estimates",
            auth=(self.username, self.password),
            headers=headers,
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "products": ",".join(self.product_ids[:limit]),
                "group_by": "product",
                "format": "json",
            },
        )
        response.raise_for_status()
        payload = response.json()
        out: list[NormalizedItem] = []
        for key, row in (payload.items() if isinstance(payload, dict) else []):
            if not isinstance(row, dict):
                continue
            product = row.get("product") or {}
            pid = str(product.get("id") or key)
            out.append(
                NormalizedItem(
                    source_type=self.name,
                    external_id=pid,
                    title=product.get("name") or f"App {pid}",
                    url=product.get("store_url"),
                    body=product.get("developer") or "Appfigures 30-day estimate",
                    author=product.get("developer"),
                    metrics={
                        "downloads_30d": row.get("downloads") or 0,
                        "revenue_30d": float(row.get("revenue") or 0),
                        "store": product.get("store"),
                    },
                    raw=row,
                )
            )
        return out[:limit]
