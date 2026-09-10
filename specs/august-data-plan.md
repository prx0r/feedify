# August Data Collection Plan

**Goal**: Full August 2026 data for all 102 X accounts in the watchlist

## Current State

| Metric | Count |
|--------|-------|
| Total accounts | 102 |
| Have August data | 9 (full) + 24 (partial) |
| No August data | 68 (have other data) |
| No data at all | 1 (@theaustinlyons) |
| Total tweets | 2,384 |
| August tweets | 163 |

## Problem

GetXAPI's search index has gaps for August. Some accounts have July/September data but not August. The `advanced_search` endpoint with `since:2026-08-01 until:2026-08-31` returns 0 results for many accounts.

## Root Cause

GetXAPI indexes tweets asynchronously. Academic/research accounts with lower tweet volume may not be fully indexed for all time periods. The `product=Latest` parameter returns whatever is currently in the index, not guaranteed complete coverage.

## Solution: Three-Phase Approach

### Phase 1: Exhaust GetXAPI (now)

Already done for all 102 accounts. Got 2,384 tweets total.

**What we have:**
- Full August: @GenAI_is_real (24), @DeepDishEnjoyer (23), @AnnaCiaunica (22), @tengyanAI (22), @advaith_sridhar (20), @ryancjulian (20), @jxmnop (17), @christinetyip (14), @ProfJohnARogers (11)
- Partial August: 24 accounts (1-9 tweets each)
- No August but have other data: 68 accounts

**Cost**: ~$0.50 total (2,384 tweets × $0.00005/tweet)

### Phase 2: Targeted August Search (next)

For the 68 accounts with no August data, try alternative search queries:

```python
# Instead of just "from:handle since:2026-08-01 until:2026-08-31"
# Try broader queries that might catch their August activity:

queries = [
    f"from:{handle} since:2026-08-01 until:2026-08-31",  # Standard
    f"from:{handle} min_faves:1 since:2026-08-01",        # Popular tweets only
    f"from:{handle} filter:media since:2026-08-01",       # Media tweets (index优先)
    f"@{handle} since:2026-08-01 until:2026-08-31",       # Mentions (someone replied to them)
]
```

**Estimated cost**: ~$0.10 (2,000 additional queries × $0.001)
**Expected yield**: 30-50% of the 68 accounts

### Phase 3: Alternative Sources (if needed)

If GetXAPI still can't find August data for specific accounts:

1. **Web search** — Google `site:x.com "handle" "August 2026"` to find cached/indexed tweets
2. **Archive.org** — Check Wayback Machine for cached X profiles
3. **Academic sources** — Many researchers post the same content on:
   - Twitter/X mirror accounts
   - Bluesky (`bsky.app`)
   - Mastodon
   - Personal websites/blogs
   - arXiv papers
   - Conference talks (YouTube)
4. **Co-author networks** — If @JunjieYe9 didn't post in August, check his co-authors' posts that mention him
5. **Paper releases** — August paper releases often come with X announcement posts

**Cost**: Minimal (web search is free)
**Expected yield**: Fills remaining gaps for high-priority accounts

## Priority Order

| Priority | Accounts | Why |
|----------|----------|-----|
| 1 | @braaannigan, @GenAI_is_real, @JunjieYe9, @msoufi_bioe, @CanAztekin | Top aithesis findings |
| 2 | @Magic3007Mai, @ZitongYang0, @YisiSang, @jxmnop | Self-improving AI cluster |
| 3 | @YanHelenZENG, @YongchaoC, @wertyfg, @nikparth1 | Autonomous science |
| 4 | @advaith_sridhar, @theanalognick, @ColesThermoAI | AI-designed hardware |
| 5 | All others | Fill in order of domain relevance |

## Implementation

Run Phase 2 now with the alternative queries. Then for any remaining gaps, use Phase 3 web search for the top 20 priority accounts.
