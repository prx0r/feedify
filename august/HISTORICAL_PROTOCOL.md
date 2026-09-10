# Historical Extraction Protocol

**Goal**: Build a complete tweet archive for all 102 X accounts, starting with August 2026 and expanding backward based on signal quality.

---

## CRITICAL LESSON: Pagination + Date Filters Required

**GetXAPI returns max 20 tweets per page.** Without pagination and date filters, you get incomplete data.

**Correct extraction pattern:**
```python
# WRONG: Only gets first page, no date filter
params = {"q": f"from:{handle}", "product": "Latest", "count": 50}

# CORRECT: Paginate AND use date filter
params = {
    "q": f"from:{handle} since:2026-08-01 until:2026-08-31",
    "product": "Latest",
    "count": 20,
    "cursor": cursor,  # from previous page
}
```

**Without pagination:**
- @GenAI_is_real: 24 August tweets (actual: 106)
- @DeepDishEnjoyer: 23 August tweets (actual: 194)
- @arthurcolle: 0 August tweets (actual: 174)

**With pagination (10 pages max):**
- @aleabitoreddit: 197 August tweets
- @DeepDishEnjoyer: 194 August tweets
- @arthurcolle: 174 August tweets
- @GenAI_is_real: 106 August tweets

---

## Phase 1: August 2026 (COMPLETE)

**Status**: Done (corrected with pagination)
**Tweets**: 1,043 from 37 accounts
**Cost**: ~$0.52

### Results (Corrected)

| Category | Accounts with August | Key Alpha |
|----------|---------------------|-----------|
| Stocks | 2/2 | @aleabitoreddit (197), @DeepDishEnjoyer (194) |
| AI research | 4/10 | @GenAI_is_real (106), @arthurcolle (174), @jxmnop (49) |
| Autonomous science | 2/10 | @bravo_abad (76), @SGRodriques (6) |
| Cognition | 2/5 | @AnnaCiaunica (55), @behaviOrganisms (5) |
| Hardware | 2/10 | @tengyanAI (33), @advaith_sridhar (23) |
| Robotics | 3/15 | @ryancjulian (27), @danfei_xu (6), @KostasPenn (2) |
| Self-improving AI | 3/10 | @christinetyip (17), @itzik009 (10), @essamsleiman (8) |
| Bio-electronics | 1/1 | @ProfJohnARogers (11) |
| Photonics | 1/1 | @theanalognick (4) |

### Decision: Who Gets July Extraction?

**Criteria for July extraction:**
1. Had August data AND it was high-signal (confidence > 0.7 on key objects)
2. OR has 20+ total tweets AND domain is high-priority
3. OR is in the aithesis top 10

**July extraction list (accounts that earned it):**

| Account | August Quality | Total Tweets | Reason for July |
|---------|---------------|--------------|-----------------|
| @GenAI_is_real | 24 aug, high alpha | 24 | Barrel Effect is core thesis |
| @braaannigan | 1 aug, high alpha | 2 | Best failure mode insights |
| @JunjieYe9 | 0 aug, but ICML paper | 11 | World model transfer is key |
| @CanAztekin | 0 aug, Science paper | 30 | Oxygen sensing = thesis proof |
| @msoufi_bioe | 0 aug, but bottom-up cells | 5 | Synthetic biology frontier |
| @advaith_sridhar | 20 aug | 32 | Materials/thermal constraints |
| @jxmnop | 17 aug | 25 | RL/self-distillation research |
| @KostasPenn | 2 aug, high alpha | 2 | VLA scaling critique |
| @TweetEdMiller | 0 aug, high alpha | 39 | Robot data economics |
| @ryancjulian | 20 aug | 32 | NVIDIA GEAR insider |
| @ZitongYang0 | 0 aug, Stanford thesis | 33 | Self-improving AI |
| @YisiSang | 0 aug, Amazon A-Evolve | 20 | Agentic data |
| @theanalognick | 2 aug | 27 | Lightmatter photonics |
| @ProfJohnARogers | 11 aug | 28 | Bio-integrated electronics |
| @nlpxuhui | 5 aug | 33 | LLM simulator falsifier |

**Total for July**: 15 accounts

---

## Phase 2: July 2026

**Target**: 15 accounts
**Estimated tweets**: ~300 (20 avg per account)
**Estimated cost**: ~$0.15
**Time**: ~5 minutes

### Process

1. Fetch July tweets for 15 accounts using GetXAPI
2. Store as `august/prima_materia/@handle.july.json`
3. Run heuristic classifier on new tweets
4. Update coverage report
5. Score each account's July alpha
6. Decide who gets June extraction

### Decision Criteria for June

Same as Phase 1, but also:
- Account must have shown CONSISTENT alpha across August AND July
- OR account is in a domain with no August data but high potential
- OR account's July data reveals a new thread worth following

---

## Phase 3: June 2026

**Target**: ~10 accounts (those who proved consistent in Aug+Jul)
**Estimated tweets**: ~200
**Estimated cost**: ~$0.10
**Time**: ~3 minutes

### Decision Criteria for Full 2-Year Extraction

After June, we have 3 months of data per account. Criteria for full extraction:

1. **Consistent signal**: Account produced high-alpha objects in 2+ of 3 months
2. **Domain coverage**: Account fills a gap in our domain coverage
3. **Source distance = 0**: Account is actually running experiments
4. **Claim quality**: Account makes specific, falsifiable claims (not generic commentary)
5. **Lead time**: Account's claims precede mainstream recognition by 3+ months

### Full Extraction List (estimated: 10-15 accounts)

These accounts get full 2-year historical extraction:
- All aithesis top 10
- Any account that showed consistent alpha in Aug+Jul+Jun
- Any account that revealed a new high-value thread

**Estimated tweets**: ~500 per account × 15 = 7,500
**Estimated cost**: ~$0.37
**Time**: ~15 minutes

---

## Phase 4: Full 2-Year Extraction

**Target**: 10-15 accounts
**Date range**: September 2024 — September 2026
**Method**: Cursor-based pagination (port from BEAR)

### Process

1. Use BEAR's cursor pagination to fetch complete timelines
2. Store as `august/prima_materia/@handle.full.json`
3. Run heuristic classifier on all tweets
4. Build per-account alpha timeline
5. Identify claim_lead_time patterns (t₀ → t₁ → t₂ → t₃)
6. Score each account's long-term value

### Output

For each account:
```
august/prima_materia/@handle.full.json
  - All tweets from Sep 2024 to Sep 2026
  - Classified by month
  - Alpha scores per tweet
  - Claim lead time tracking
```

---

## Cost Summary

| Phase | Accounts | Tweets | Cost | Time |
|-------|----------|--------|------|------|
| Phase 1: August | 102 | 2,384 | $0.50 | Done |
| Phase 2: July | 15 | ~300 | $0.15 | 5 min |
| Phase 3: June | 10 | ~200 | $0.10 | 3 min |
| Phase 4: Full 2-year | 15 | ~7,500 | $0.37 | 15 min |
| **Total** | | **~10,400** | **~$1.12** | **~25 min** |

---

## Quality Gates

After each phase, review:

1. **Object count**: Are we creating meaningful objects? (target: 5+ per account per month)
2. **Edge count**: Are we connecting related posts? (target: 2+ edges per account per month)
3. **Alpha scores**: Are high-alpha objects actually insightful? (target: avg > 0.5)
4. **Domain coverage**: Are all 11 domains represented?
5. **Claim classification**: Are we getting theories/problems/observations, not just claims?

If quality is low for an account, drop them from further extraction.

---

## File Structure

```
august/
├── prima_materia/
│   ├── @handle.json          # August tweets
│   ├── @handle.july.json     # July tweets (Phase 2)
│   ├── @handle.june.json     # June tweets (Phase 3)
│   └── @handle.full.json     # Full 2-year (Phase 4)
├── categories/
│   ├── 01-self-improving-ai.md
│   ├── ...
│   └── 11-stocks.md
├── analysis/
│   ├── coverage-report.md
│   ├── alpha-summary.md
│   └── gaps.md
├── EXTRACTION_PLAN.md
└── HISTORICAL_PROTOCOL.md    # This file
```
