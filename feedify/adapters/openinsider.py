"""OpenInsider adapter — corporate insider transaction discovery.

OpenInsider is a clean, structured source for insider transactions.
It's particularly useful for:
- Cluster purchases (multiple insiders buying)
- CEO/CFO buys
- Large relative ownership increases
- Repeat purchases
- Unusual purchase sizes

Unlike raw EDGAR, OpenInsider pre-filters and structures the data.
We use it as a Tier 1 enrichment source (10% weight).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx

from feedify.schemas import NormalizedItem

from .base import SourceAdapter

OPENINSIDER_BASE = "http://openinsider.com"


class OpenInsiderAdapter(SourceAdapter):
    """OpenInsider — structured insider transaction data."""

    name = "openinsider"

    async def fetch_screener(self, params: dict | None = None) -> list[dict]:
        """Fetch from OpenInsider's screener."""
        url = f"{OPENINSIDER_BASE}/screener"
        resp = await self.client.get(url, params=params or {}, timeout=30)
        resp.raise_for_status()
        # OpenInsider returns HTML; parse the table
        return self._parse_html_table(resp.text)

    def _parse_html_table(self, html: str) -> list[dict]:
        """Parse OpenInsider HTML table — the real table structure."""
        rows = []
        # Find rows in the tinytable with insider data
        # Pattern: <tr style="background:..."><td...>TC</td><td...>filing</td><td...>trade</td><td...>TICKER</td>...
        for match in re.finditer(r'<tr[^>]*style="background:(?:#[a-f0-9]+)"[^>]*>(.*?)</tr>', html, re.S):
            cells = re.findall(r'<td[^>]*>(.*?)</td>', match.group(1), re.S)
            if len(cells) >= 12:
                # Strip HTML tags
                clean = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                
                # Extract ticker from the link
                ticker_match = re.search(r'href="/([A-Z]{1,5})"', match.group(1))
                ticker = ticker_match.group(1) if ticker_match else ""
                
                if not ticker:
                    continue
                
                # Extract insider name from the link
                insider_match = re.search(r'href="/insider/[^"]*"[^>]*>([^<]+)</a>', match.group(1))
                insider_name = insider_match.group(1).strip() if insider_match else ""
                
                # Extract SEC link
                sec_match = re.search(r'href="(http://www\.sec\.gov/[^"]+)"', match.group(1))
                sec_url = sec_match.group(1) if sec_match else ""
                
                # Parse fields
                txn_code = clean[0] if len(clean) > 0 else ""  # TC
                filing_date = clean[1] if len(clean) > 1 else ""  # filing
                trade_date = clean[2] if len(clean) > 2 else ""  # trade
                # clean[3] is ticker (already extracted)
                # clean[4] is insider name (already extracted)
                title = clean[5] if len(clean) > 5 else ""  # Dir, EVP, etc
                trade_type = clean[6] if len(clean) > 6 else ""  # S - Sale, P - Purchase
                price = clean[7] if len(clean) > 7 else ""  # $222.26
                shares = clean[8] if len(clean) > 8 else ""  # -1,848,501
                owned = clean[9] if len(clean) > 9 else ""  # 29,921,132
                change = clean[10] if len(clean) > 10 else ""  # -6%
                value = clean[11] if len(clean) > 11 else ""  # -$410,843,671
                
                rows.append({
                    "ticker": ticker,
                    "insider_name": insider_name,
                    "title": title,
                    "trade_type": trade_type,
                    "price": price,
                    "shares": shares,
                    "owned": owned,
                    "change": change,
                    "value": value,
                    "filing_date": filing_date,
                    "trade_date": trade_date,
                    "sec_url": sec_url,
                    "txn_code": txn_code,
                })
        return rows

    def normalize(self, row: dict) -> NormalizedItem | None:
        """Normalize an OpenInsider row into a NormalizedItem."""
        ticker = row.get("ticker", "")
        if not ticker or ticker == "---":
            return None

        insider = row.get("insider_name", "Unknown")
        title = row.get("title", "")
        trade_type = row.get("trade_type", "")
        price_str = row.get("price", "0").replace("$", "").replace(",", "")
        shares_str = row.get("shares", "0").replace(",", "").replace("+", "")
        value_str = row.get("value", "0").replace("$", "").replace(",", "").replace("-", "")
        change = row.get("change", "")
        sec_url = row.get("sec_url", "")

        try:
            price = float(price_str) if price_str else 0
            shares = int(shares_str) if shares_str else 0
            value = float(value_str) if value_str else 0
        except (ValueError, TypeError):
            price, shares, value = 0, 0, 0

        # Determine if this is a purchase or sale
        is_purchase = "P" in trade_type.upper() or "purchase" in trade_type.lower()
        action = "purchased" if is_purchase else "sold"

        display_title = f"{ticker} — {insider} — ${abs(value):,.0f} {trade_type}"
        summary = (
            f"{insider} ({title}) {action} {abs(shares):,} shares of {ticker} "
            f"at ${price:.2f}/share for ${abs(value):,.0f}."
        )

        metrics = {
            "filing_type": "4",
            "reporting_owner": insider,
            "issuer_ticker": ticker,
            "issuer_name": "",
            "transaction_code": row.get("txn_code", trade_type[0] if trade_type else ""),
            "transaction_label": trade_type,
            "shares": shares,
            "price_per_share": price,
            "total_value": value,
            "ownership_change": change,
            "filing_date": row.get("filing_date"),
            "trade_date": row.get("trade_date"),
            "sec_url": sec_url,
            "source": "openinsider",
        }

        return NormalizedItem(
            source_type=self.name,
            external_id=f"openinsider-{ticker}-{insider}-{row.get('trade_date', '')}",
            title=display_title[:200],
            url=sec_url or f"http://openinsider.com/search?q={ticker}",
            body=summary,
            author=insider,
            published_at=datetime.now(timezone.utc),
            metrics=metrics,
            raw=row,
        )

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        """Fetch recent insider transactions from OpenInsider."""
        items = []
        try:
            # Fetch latest cluster buys (highest signal)
            rows = await self.fetch_screener({"s": "o", "t": "0", "plc": "0"})
            for row in rows:
                item = self.normalize(row)
                if item:
                    items.append(item)
                if len(items) >= limit:
                    break
        except Exception:
            pass
        return items
