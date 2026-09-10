# Feedify × BEAR Integration Plan

**Date**: 2026-09-10
**Status**: Future — not blocking current work

## What BEAR Is

BEAR (`/root/BEAR`) is a crypto trading intelligence engine that:
- Scrapes X data from specific crypto traders via GetXAPI
- Tracks prediction accuracy (win rates) per trader per strategy
- Crystallizes strategies from social signals
- Uses LLM to decide when strategies should be active (ON/OFF)

## What's Compatible

| Component | BEAR | Feedify | Action |
|-----------|------|---------|--------|
| GetXAPI provider | Cursor-based pagination, fetches full timelines | First-page only (50 tweets max) | **Port BEAR's pagination to Feedify** |
| Tweet data model | `Tweet` dataclass | `NormalizedItem` | Same fields, no change needed |
| Signal crystallization | Strategies from trader predictions | Objects + Edges | BEAR's STRAT pattern maps to our convergence detection |
| Win rate tracking | Prediction accuracy per trader | claim_lead_time (t₀→t₁→t₂→t₃) | Wire BEAR's accuracy tracking into our Interaction model |
| LLM activation | Agent reads tweets → ON/OFF strategies | Compiled feed pipeline | Same pattern, different domain |

## What To Port

### 1. Cursor-based pagination (HIGH PRIORITY)
BEAR's `GetXAPI.user_posts()` uses `cursor` param to fetch complete timelines. Our `XAdapter` only gets first page.

```python
# BEAR's approach (better)
params = {"q": f"from:{username}", "product": "Latest", "count": 20, "cursor": cursor}
# Returns next_cursor + has_next_page for pagination

# Our current approach (limited)
params = {"q": f"from:{handle}", "product": "Latest", "count": 50}
# Only gets first 50 tweets
```

**Impact**: Fixes the "4 of 10 accounts returned 0 August tweets" problem.

### 2. Trader accuracy tracking
BEAR tracks: `trader → prediction → outcome → win_rate`

Maps to our model:
```
Object (prediction) → Interaction (DONE) → Object version update → lead_time
```

Wire BEAR's accuracy tracking into our Interaction model.

### 3. Strategy crystallization
BEAR's STRAT pattern:
```
When trader A says X AND trader B says Y → strategy ON
```

Maps to our convergence detection:
```
When source_distance=0 account A posts theory AND source_distance=0 account B posts supporting evidence → high-alpha signal
```

### 4. Regime detection
BEAR's market regime (UP/DOWN/RANGE) maps to our domain classification + confidence scoring.

## Integration Points

### Data Flow
```
Feedify (X extraction, 102 accounts, 10 domains)
    ↓
    Object/Edge graph
    ↓
    BEAR reads graph for crypto-relevant objects
    ↓
    BEAR crystallizes strategies from Feedify objects
    ↓
    BEAR activation rules decide ON/OFF
```

### Shared GetXAPI Key
Both projects use the same GetXAPI key. Could share credits.

### Shared Tweet Model
BEAR's `Tweet` dataclass is compatible with our `NormalizedItem`. No conversion needed.

## When To Do This

After:
1. ✅ Feedify August extraction is complete
2. ✅ LLM compiler is working on all accounts
3. ⬜ Convergence detection is wired into Feedify
4. ⬜ claim_lead_time tracking is automated

Then:
- Port BEAR's cursor pagination to Feedify X adapter
- Wire BEAR's accuracy tracking into Feedify Interactions
- Create shared `Tweet`/`NormalizedItem` adapter

## Files To Reference

- `/root/BEAR/src/bear/social/x_reader.py` — Tweet dataclass, XProvider interface
- `/root/BEAR/src/bear/social/providers/getxapi.py` — GetXAPI with cursor pagination
- `/root/BEAR/HANDOVER.md` — BEAR's architecture and current state
- `/root/BEAR/AGENTS.md` — BEAR's control plane (similar to our AGENTS.md)
