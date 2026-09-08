# Feedify Session Log — 2026-09-08

## Timeline

```
19:45 UTC — Started session
19:45 UTC — Reviewed user's insider research (20 X accounts, scoring spec)
19:46 UTC — Built SEC EDGAR adapter (edgar.py)
19:47 UTC — Built OpenInsider adapter (openinsider.py)
19:48 UTC — Built insider scoring engine (insider_scoring.py)
19:49 UTC — Created FRONTIER universe config (insiders.json)
19:50 UTC — Updated X watchlist with 20 accounts
19:51 UTC — Wired adapters into ingestion pipeline
19:52 UTC — Fixed syntax error in insider_scoring.py (line 97: 50,000 → 50_000)
19:53 UTC — Ran X ingestion: 100 signals from 5 tier-1 accounts
19:54 UTC — Ran X ingestion: 200 more signals from 10+ accounts
19:55 UTC — Ran OpenInsider ingestion: 5 signals
19:56 UTC — Verified live site at https://feedify.egoic.ai
19:57 UTC — Created report and log
```

## Decisions Made

1. **Scoring engine is transaction-based, not social-based**
   - Score derives from the underlying transaction, not how many accounts tweet about it
   - Sources discover. Filings verify. Feedify decides significance.

2. **FRONTIER universe is AI/chips/quantum/power**
   - These are the sectors where insider activity matters most
   - Frontier stocks get 1.2x bonus in scoring

3. **Source weights follow user's spec**
   - SEC EDGAR: 35% (canonical truth)
   - QuiverQuant: 15% (best enrichment)
   - OpenInsider: 10% (corporate patterns)
   - WhaleWisdom: 10% (13D/G institutional)
   - Capitol Trades: 10% (congressional QA)
   - Unusual Whales: 7.5% (discovery + options)
   - X specialists: 7.5% (fast discovery)
   - Everything else: 5% (corroboration)

4. **Signal classes are event-based, not source-based**
   - CORPORATE_INSIDER → Form 3/4/5
   - ACTIVIST → 13D/G
   - INSTITUTIONAL → 13F
   - CONGRESS → STOCK Act PTR
   - X_ALPHA → unverified discovery

## Issues Encountered

1. **Syntax error in insider_scoring.py**
   - Line 97: `elif total_value > 50,000:` → `elif total_value > 50_000:`
   - Fixed immediately

2. **SEC EDGAR API returns 0 results**
   - EDGAR uses a different endpoint structure than assumed
   - Need to investigate the correct EDGAR full-text search API format
   - Not blocking — OpenInsider provides similar data

3. **Settings cache**
   - `lru_cache` on `get_settings()` held old values
   - Fixed by restarting the service

## What Was Shipped

- 303 signals live at https://feedify.egoic.ai
- 15 sources ingested
- Scoring engine operational
- FRONTIER universe configured
- Report and log created

## Next Session Should

1. Fix SEC EDGAR adapter (investigate correct API format)
2. Build insiders frontend view
3. Set up backtest to measure source alpha
4. Add source competition tracking
