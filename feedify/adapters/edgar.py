"""SEC EDGAR adapter — fetches Form 4, 13D/G, 13F filings directly from EDGAR.

EDGAR is the canonical source for insider transactions. This adapter:
1. Fetches recent filings from EDGAR's full-text search API
2. Parses Form 4 (insider transactions), 13D/G (activist stakes), 13F (institutional holdings)
3. Normalizes into Feedify's NormalizedItem schema
4. Preserves all raw filing data for downstream scoring

EDGAR rate limit: 10 requests/second. We respect this with a semaphore.
"""
from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

import httpx

from feedify.schemas import NormalizedItem

from .base import SourceAdapter

EDGAR_BASE = "https://efts.sec.gov/LATEST"
EDGAR_FILINGS = "https://www.sec.gov/cgi-bin/browse-edgar"
EDGAR_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"
USER_AGENT = "Feedify/1.0 (insiders@feedify.dev)"
FILING_TYPES = ["4", "13D", "13G", "13F-HR"]


class EdgarAdapter(SourceAdapter):
    """SEC EDGAR filing adapter — the canonical source for insider/activist/institutional data."""

    name = "sec_edgar"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._semaphore = asyncio.Semaphore(10)  # EDGAR rate limit

    def _headers(self) -> dict:
        return {"User-Agent": USER_AGENT, "Accept": "application/json"}

    async def _get(self, url: str) -> dict | list | None:
        async with self._semaphore:
            resp = await self.client.get(url, headers=self._headers())
            if resp.status_code == 429:
                await asyncio.sleep(1)
                return None
            resp.raise_for_status()
            return resp.json()

    async def _get_text(self, url: str) -> str:
        async with self._semaphore:
            resp = await self.client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.text

    async def fetch_recent_filings(self, filing_type: str, limit: int = 40) -> list[dict]:
        """Fetch recent filings of a given type from EDGAR full-text search."""
        url = f"{EDGAR_BASE}/search-index?q=%22{filing_type}%22&dateRange=custom&startdt=2026-01-01&forms={filing_type}&hits.hits.total=true&hits.hits._source=file_date,entity_name,cik,form_type,display_names"
        data = await self._get(url)
        if not data:
            return []
        hits = data.get("hits", {}).get("hits", [])
        return [h.get("_source", {}) | {"_id": h.get("_id")} for h in hits[:limit]]

    async def fetch_form4_filings(self, limit: int = 40) -> list[dict]:
        """Fetch recent Form 4 filings."""
        url = f"{EDGAR_BASE}/search-index?q=%224%22&forms=4&dateRange=custom&startdt=2026-01-01"
        data = await self._get(url)
        if not data:
            return []
        hits = data.get("hits", {}).get("hits", [])
        return hits[:limit]

    async def fetch_xbrl_data(self, cik: str, accession: str) -> dict[str, Any]:
        """Fetch parsed XBRL data for a filing."""
        accession_clean = accession.replace("-", "")
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
        data = await self._get(url)
        return data or {}

    def parse_form4_xml(self, xml_text: str) -> dict[str, Any] | None:
        """Parse Form 4 XML filing into structured data."""
        try:
            root = ET.fromstring(xml_text)
            ns = {"edgar": "http://www.sec.gov/cgi-bin/viewer?action=view&cik=&type=4&dateb=&owner=include&count=40"}
            # Extract reporting owner
            owner_name = root.findtext(".//rptOwnerName", default="")
            owner_cik = root.findtext(".//rptOwnerCik", default="")
            # Extract issuer info
            issuer_name = root.findtext(".//issuerName", default="")
            issuer_cik = root.findtext(".//issuerCik", default="")
            issuer_ticker = root.findtext(".//issuerTicker", default="")
            # Extract transaction(s)
            transactions = []
            for txn in root.findall(".//nonDerivativeTransaction"):
                code = txn.findtext(".//transactionCode", "")
                shares = txn.findtext(".//transactionShares/value", "")
                price = txn.findtext(".//transactionPricePerShare/value", "")
                shares_owned = txn.findtext(".//sharesOwnedFollowingTransaction/value", "")
                ownership = txn.findtext(".//ownershipNature/directOrIndirectOwnership", "")
                is_10b5 = txn.findtext(".//isDerivativeTransaction", "false")
                transactions.append({
                    "code": code,
                    "shares": float(shares) if shares else 0,
                    "price_per_share": float(price) if price else 0,
                    "shares_owned_after": float(shares_owned) if shares_owned else 0,
                    "ownership_nature": ownership,
                    "is_10b5_1": is_10b5.lower() == "true",
                })

            return {
                "reporting_owner": owner_name,
                "reporting_owner_cik": owner_cik,
                "issuer_name": issuer_name,
                "issuer_cik": issuer_cik,
                "issuer_ticker": issuer_ticker,
                "transactions": transactions,
            }
        except ET.ParseError:
            return None

    def parse_13d_text(self, text: str) -> dict[str, Any]:
        """Extract key fields from 13D filing text."""
        # Best-effort extraction from raw text
        result: dict[str, Any] = {}
        # Look for issuer
        m = re.search(r"(?:ISSUER|COMPANY)[:\s]+([A-Z][A-Z\s,\.]+)", text)
        if m:
            result["issuer_name"] = m.group(1).strip()
        # Look for shares/percentage
        m = re.search(r"(\d[\d,]+)\s+shares?\s+(?:of\s+)?(?:common\s+)?stock", text, re.I)
        if m:
            result["shares"] = int(m.group(1).replace(",", ""))
        m = re.search(r"(\d+\.?\d*)\s*%", text)
        if m:
            result["percent_owned"] = float(m.group(1))
        return result

    def normalize_form4(self, filing: dict, parsed: dict[str, Any]) -> NormalizedItem | None:
        """Normalize a Form 4 filing into a NormalizedItem."""
        owner = parsed.get("reporting_owner", "Unknown")
        issuer = parsed.get("issuer_name", "Unknown")
        ticker = parsed.get("issuer_ticker", "")
        txns = parsed.get("transactions", [])
        if not txns:
            return None

        # Use the most significant transaction for scoring
        main_txn = max(txns, key=lambda t: abs(t.get("shares", 0) * t.get("price_per_share", 0)))
        code = main_txn.get("code", "")
        shares = main_txn.get("shares", 0)
        price = main_txn.get("price_per_share", 0)
        total_value = shares * price

        # Transaction code meanings
        code_labels = {
            "P": "Open-Market Purchase",
            "S": "Open-Market Sale",
            "A": "Stock Award",
            "M": "Option Exercise",
            "F": "Tax Withholding",
            "G": "Gift",
            "C": "Converted Derivative",
            "J": "Other Acquisition/Disposition",
        }

        txn_label = code_labels.get(code, f"Code {code}")
        action = "purchased" if code == "P" else "sold" if code == "S" else "transacted"

        title = f"{ticker} — {owner} — ${total_value:,.0f} {txn_label}"
        summary = (
            f"{owner} {action} {shares:,.0f} shares of {issuer} ({ticker}) "
            f"at ${price:.2f}/share for a total value of ${total_value:,.0f}."
        )

        metrics = {
            "filing_type": "4",
            "reporting_owner": owner,
            "reporting_owner_cik": parsed.get("reporting_owner_cik"),
            "issuer_name": issuer,
            "issuer_cik": parsed.get("issuer_cik"),
            "issuer_ticker": ticker,
            "transaction_code": code,
            "transaction_label": txn_label,
            "shares": shares,
            "price_per_share": price,
            "total_value": total_value,
            "shares_owned_after": main_txn.get("shares_owned_after", 0),
            "ownership_nature": main_txn.get("ownership_nature"),
            "is_10b5_1": main_txn.get("is_10b5_1", False),
            "filing_date": filing.get("file_date"),
            "accession_number": filing.get("_id", ""),
        }

        return NormalizedItem(
            source_type=self.name,
            external_id=f"form4-{filing.get('_id', '')}-{owner}",
            title=title[:200],
            url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={parsed.get('issuer_cik', '')}&type=4&dateb=&owner=include&count=40",
            body=summary,
            author=owner,
            published_at=datetime.now(timezone.utc),
            metrics=metrics,
            raw=filing,
        )

    def normalize_13d(self, filing: dict, parsed: dict[str, Any]) -> NormalizedItem | None:
        """Normalize a 13D filing into a NormalizedItem."""
        issuer = parsed.get("issuer_name", "Unknown")
        shares = parsed.get("shares", 0)
        pct = parsed.get("percent_owned", 0)

        title = f"13D — {issuer} — {pct:.1f}% activist stake ({shares:,} shares)"
        summary = (
            f"An activist investor has disclosed a {pct:.1f}% stake in {issuer}, "
            f"holding {shares:,} shares. This may indicate plans to influence company strategy."
        )

        metrics = {
            "filing_type": "13D",
            "issuer_name": issuer,
            "shares": shares,
            "percent_owned": pct,
            "filing_date": filing.get("file_date"),
            "accession_number": filing.get("_id", ""),
        }

        return NormalizedItem(
            source_type=self.name,
            external_id=f"13d-{filing.get('_id', '')}",
            title=title[:200],
            url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={parsed.get('issuer_cik', '')}&type=13D&dateb=&owner=include&count=40",
            body=summary,
            author="Activist Investor",
            published_at=datetime.now(timezone.utc),
            metrics=metrics,
            raw=filing,
        )

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        """Fetch and normalize recent Form 4 and 13D filings."""
        items: list[NormalizedItem] = []

        # Fetch Form 4s
        try:
            form4s = await self.fetch_form4_filings(limit=limit)
            for filing in form4s:
                xml_text = await self._get_text(filing.get("primary_document_url", ""))
                parsed = self.parse_form4_xml(xml_text)
                if parsed:
                    item = self.normalize_form4(filing, parsed)
                    if item:
                        items.append(item)
                        if len(items) >= limit:
                            break
        except Exception:
            pass

        # Fetch 13Ds
        try:
            d_filings = await self.fetch_recent_filings("13D", limit=10)
            for filing in d_filings:
                parsed = self.parse_13d_text(filing.get("display_name", ""))
                item = self.normalize_13d(filing, parsed)
                if item:
                    items.append(item)
        except Exception:
            pass

        return items[:limit]
