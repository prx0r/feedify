from __future__ import annotations

from feedify.schemas import NormalizedItem
from feedify.settings import get_settings

from .base import SourceAdapter
from .utils import parse_datetime


class TrustMRRAdapter(SourceAdapter):
    name = "trustmrr"
    base_url = "https://trustmrr.com/api/v1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = get_settings().trustmrr_api_key

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        if not self.configured:
            return []
        headers = {"Authorization": f"Bearer {self.api_key}"}
        items: list[NormalizedItem] = []
        page = 1
        while len(items) < limit:
            response = await self.client.get(
                f"{self.base_url}/startups",
                headers=headers,
                params={"sort": "growth-desc", "limit": min(10, limit - len(items)), "page": page},
            )
            response.raise_for_status()
            payload = response.json()
            for row in payload.get("data", []):
                revenue = row.get("revenue") or {}
                slug = row.get("slug") or row.get("name")
                items.append(
                    NormalizedItem(
                        source_type=self.name,
                        external_id=str(slug),
                        title=row.get("name") or str(slug),
                        url=row.get("website") or f"https://trustmrr.com/startup/{slug}",
                        body=row.get("description"),
                        author=row.get("xHandle"),
                        published_at=parse_datetime(row.get("foundedDate")),
                        metrics={
                            "last30d_revenue_cents": revenue.get("last30Days") or 0,
                            "mrr_cents": revenue.get("mrr") or 0,
                            "total_revenue_cents": revenue.get("total") or 0,
                            "growth30d": row.get("growth30d"),
                            "growth_mrr30d": row.get("growthMRR30d"),
                            "customers": row.get("customers") or 0,
                            "asking_price_cents": row.get("askingPrice"),
                            "multiple": row.get("multiple"),
                            "rank": row.get("rank"),
                            "visitors30d": row.get("visitorsLast30Days"),
                            "revenue_per_visitor": row.get("revenuePerVisitor"),
                            "on_sale": bool(row.get("onSale")),
                            "category": row.get("category"),
                            "target_audience": row.get("targetAudience"),
                        },
                        raw=row,
                    )
                )
            meta = payload.get("meta") or {}
            if not meta.get("hasMore") or not payload.get("data"):
                break
            page += 1
        return items[:limit]
