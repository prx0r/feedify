from __future__ import annotations

import csv
import io
import time
from typing import Any

import httpx

# Ticker -> Stooq symbol. Crypto rides CoinGecko instead.
STOOQ_SYMBOLS = {
    "GFS": "gfs.us",
    "FORM": "form.us",
    "KEYS": "keys.us",
    "COHR": "cohr.us",
    "LITE": "lite.us",
    "IONQ": "ionq.us",
    "QNT": "qnt.us",
    "RGTI": "rgti.us",
    "QBTS": "qbts.us",
    "OXIG": "oxig.uk",
}

# CoinGecko ids for the crypto leg.
COINGECKO_IDS = {
    "ETH": "ethereum",
    "QRL": "quantum-resistant-ledger",
    "QANX": "qanplatform",
    "CELL": "cellframe",
}

CACHE_TTL_S = 15 * 60
_cache: dict[str, tuple[float, dict]] = {}


def _cached(key: str, loader):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL_S:
        return hit[1]
    try:
        data = loader()
    except Exception:
        return hit[1] if hit else {}
    _cache[key] = (now, data)
    return data


def _stooq_moves(tickers: list[str]) -> dict[str, dict]:
    symbols = {t: STOOQ_SYMBOLS[t] for t in tickers if t in STOOQ_SYMBOLS}
    if not symbols:
        return {}

    def load():
        out: dict[str, dict] = {}
        # Daily history per symbol (q/l has no previous close).
        # Free and keyless; 15-min cache keeps briefs cheap.
        for ticker, symbol in symbols.items():
            try:
                resp = httpx.get(
                    "https://stooq.com/q/d/l/",
                    params={"s": symbol, "d1": "20000101",
                            "d2": "21000101", "i": "d"},
                    timeout=20,
                    follow_redirects=True,
                )
                resp.raise_for_status()
                rows = [r for r in csv.DictReader(io.StringIO(resp.text))
                        if r.get("Close")]
                if len(rows) < 2:
                    continue
                prev = float(rows[-2]["Close"])
                row = rows[-1]
                close = float(row["Close"])
                if prev <= 0 or close <= 0:
                    continue
                out[ticker] = {
                    "price": round(close, 2),
                    "pct_1d": round((close - prev) / prev * 100, 2),
                    "asof": row.get("Date"),
                    "venue": "stooq",
                }
            except Exception:
                continue
        return out

    return _cached("stooq:" + ",".join(sorted(symbols)), load)


def _coingecko_moves(tickers: list[str]) -> dict[str, dict]:
    ids = {t: COINGECKO_IDS[t] for t in tickers if t in COINGECKO_IDS}
    if not ids:
        return {}

    def load():
        out: dict[str, dict] = {}
        resp = httpx.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ",".join(ids.values()), "vs_currencies": "usd",
                    "include_24hr_change": "true"},
            timeout=20,
        )
        resp.raise_for_status()
        body = resp.json()
        for ticker, cid in ids.items():
            row = body.get(cid) or {}
            if "usd" not in row:
                continue
            out[ticker] = {
                "price": row["usd"],
                "pct_1d": round(float(row.get("usd_24h_change") or 0), 2),
                "asof": "coingecko",
                "venue": "coingecko",
            }
        return out

    return _cached("coingecko:" + ",".join(sorted(ids)), load)


def get_moves(tickers: list[str]) -> dict[str, dict[str, Any]]:
    """Latest price + 1d move per ticker. Never raises; missing = absent."""
    tickers = [t.upper() for t in tickers]
    moves: dict[str, dict] = {}
    moves.update(_stooq_moves(tickers))
    moves.update(_coingecko_moves(tickers))
    return moves


def unmoved(tickers: list[str], threshold_pct: float = 2.0) -> list[str]:
    """Tickers whose 1d move is flat — repricing may not have happened yet."""
    moves = get_moves(tickers)
    return [t for t in tickers if t in moves and abs(moves[t]["pct_1d"]) < threshold_pct]
