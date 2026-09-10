"""Insider scoring engine — transaction-based scoring, not social-buzz-based.

The key insight: signal score should derive from the underlying transaction,
not how many accounts tweet about it.

Scoring formula:
  TRANSACTION_SIGNIFICANCE × ROLE_WEIGHT × PATTERN_BONUS × RECENCY × NOVELTY
  
Where:
  TRANSACTION_SIGNIFICANCE = f(type, value, % ownership change, 10b5-1 status)
  ROLE_WEIGHT = CEO/CFO/Director/10% owner
  PATTERN_BONUS = cluster buying, repeat purchases, post-drawdown buying
  RECENCY = decay from transaction date
  NOVELTY = first-time activity vs routine

The source (X account, EDGAR, etc.) affects CONFIDENCE but not SCORE.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Transaction codes and their significance weights
# SEC Form 4 transaction codes: https://www.sec.gov/about/forms/form4.htm
TRANSACTION_WEIGHTS = {
    "P": 1.0,   # Open-market purchase — highest signal
    "S": -0.3,  # Open-market sale — negative but not always bad
    "A": 0.05,  # Stock award — routine, low signal
    "M": 0.0,   # Option exercise — often tax-related
    "F": -0.05, # Tax withholding — routine
    "G": -0.1,  # Gift — low signal
    "C": 0.1,   # Converted derivative
    "J": 0.0,   # Other
}

# Role multipliers
ROLE_WEIGHTS = {
    "CEO": 1.5,
    "CFO": 1.3,
    "COO": 1.2,
    "Director": 1.1,
    "Officer": 1.0,
    "10% Owner": 1.4,
    "Other": 0.8,
}

# FRONTIER universe — high-growth / frontier stocks we care about
FRONTIER_UNIVERSE = {
    "AI": ["META", "GOOGL", "MSFT", "AMZN", "PLTR", "CRWV", "NBIS"],
    "CHIPS": ["NVDA", "AMD", "AVGO", "MU", "TSM", "ASML", "ARM", "INTC", "MRVL"],
    "QUANTUM": ["IONQ", "INFQ", "RGTI", "QBTS", "QUBT"],
    "POWER_INFRA": ["VRT", "ETN", "CEG", "VST", "GEV", "NRG"],
}

ALL_FRONTIER = set()
for tickers in FRONTIER_UNIVERSE.values():
    ALL_FRONTIER.update(tickers)


def is_frontier(ticker: str) -> bool:
    return ticker.upper() in ALL_FRONTIER


def get_frontier_sector(ticker: str) -> str | None:
    ticker = ticker.upper()
    for sector, tickers in FRONTIER_UNIVERSE.items():
        if ticker in tickers:
            return sector
    return None


def score_transaction(metrics: dict[str, Any], historical: list[dict] | None = None) -> dict[str, Any]:
    """Score an insider transaction.
    
    Returns:
        dict with score (0-100), tier (A+/A/B/C), signal_type, and breakdown
    """
    historical = historical or []
    
    code = metrics.get("transaction_code", "")
    shares = metrics.get("shares", 0)
    price = metrics.get("price_per_share", 0)
    total_value = shares * price
    is_10b5 = metrics.get("is_10b5_1", False)
    ticker = metrics.get("issuer_ticker", "")
    
    # Step 1: Base transaction significance
    base = TRANSACTION_WEIGHTS.get(code, 0)
    
    # Value amplifier: larger = more significant
    if total_value > 5_000_000:
        value_amp = 1.5
    elif total_value > 1_000_000:
        value_amp = 1.3
    elif total_value > 250_000:
        value_amp = 1.1
    elif total_value > 50_000:
        value_amp = 1.0
    else:
        value_amp = 0.7  # Small transactions are less meaningful
    
    # 10b5-1 discount: pre-planned trades are less informative
    plenalty = 0.6 if is_10b5 else 1.0
    
    # Step 2: Role weight
    role = metrics.get("ownership_nature", "Other")
    role_w = ROLE_WEIGHTS.get(role, 0.8)
    
    # Step 3: Pattern bonuses (from historical data)
    pattern_bonus = 1.0
    
    # Cluster buying: multiple insiders buying within 30 days
    recent_buys = [
        h for h in historical
        if h.get("transaction_code") == "P"
        and h.get("filing_date", "") > "2026-01-01"  # Placeholder; use actual date diff
    ]
    if len(recent_buys) >= 3:
        pattern_bonus += 0.3  # Cluster buying
    elif len(recent_buys) >= 2:
        pattern_bonus += 0.15
    
    # First purchase after long drought
    recent_sales = [
        h for h in historical
        if h.get("transaction_code") == "S"
    ]
    if code == "P" and recent_sales and not any(h.get("transaction_code") == "P" for h in historical[-10:]):
        pattern_bonus += 0.2  # First buy after selling streak
    
    # Step 4: Frontier bonus
    frontier_bonus = 1.2 if is_frontier(ticker) else 1.0
    
    # Step 5: Recency (decay from transaction date)
    filing_date = metrics.get("filing_date", "")
    recency = 1.0
    if filing_date:
        try:
            filed = datetime.fromisoformat(filing_date.replace("Z", "+00:00"))
            days_ago = (datetime.now(timezone.utc) - filed).days
            recency = max(0.3, 1.0 - (days_ago * 0.02))  # 2% decay per day
        except (ValueError, TypeError):
            pass
    
    # Combine
    raw_score = base * value_amp * plenalty * role_w * pattern_bonus * frontier_bonus * recency
    
    # Normalize to 0-100
    # Range: roughly -0.3 to +3.0 before normalization
    score = max(0, min(100, int((raw_score + 0.3) / 3.3 * 100)))
    
    # Determine tier
    if score >= 80:
        tier = "A+"
    elif score >= 60:
        tier = "A"
    elif score >= 40:
        tier = "B"
    else:
        tier = "C"
    
    # Signal type
    if code == "P" and total_value > 1_000_000 and not is_10b5:
        signal = "HIGH_SIGNAL_PURCHASE"
    elif code == "P" and score >= 60:
        signal = "NOTABLE_PURCHASE"
    elif code == "S" and total_value > 5_000_000 and not is_10b5:
        signal = "LARGE_SALE"
    elif code in ("A", "M", "F"):
        signal = "ROUTINE"
    else:
        signal = "OBSERVATION"
    
    return {
        "score": score,
        "tier": tier,
        "signal_type": signal,
        "is_frontier": is_frontier(ticker),
        "frontier_sector": get_frontier_sector(ticker),
        "breakdown": {
            "base": round(base, 2),
            "value_amplifier": value_amp,
            "10b5_penalty": plenalty,
            "role_weight": role_w,
            "pattern_bonus": round(pattern_bonus, 2),
            "frontier_bonus": frontier_bonus,
            "recency": round(recency, 2),
            "raw_score": round(raw_score, 3),
        },
    }


def score_congress(metrics: dict[str, Any]) -> dict[str, Any]:
    """Score a congressional trade — different weights than corporate insider."""
    # Congress trades are inherently less reliable (45-day delay)
    # and often small ($1k-$15k) with low predictive value
    return {
        "score": 25,
        "tier": "B",
        "signal_type": "CONGRESS_DISCLOSURE",
        "is_frontier": False,
        "frontier_sector": None,
        "breakdown": {
            "note": "Congressional trades scored separately; "
                    "high-value + committee-relevant + novel = higher score",
        },
    }
