# Session Review: Feedify 2.0 Progress

**Date**: 2026-09-10
**Duration**: Full day session

---

## What We Built Today

### 1. Feedify 2.0 — Complete Data Model Rewrite

Replaced flat signals with a knowledge graph:

| Table | Purpose |
|-------|---------|
| `artifacts` | Immutable inputs (tweets, filings) — replaces `source_records` |
| `objects` | Versioned knowledge (theories, problems, predictions) — replaces `signals` |
| `edges` | Relationships between objects (supports, contradicts, related_to) |
| `feeds` | Versioned attention programs (added `version`, `forked_from_id`) |
| `interactions` | User actions (DONE/SAVE/FOLLOW/NOISE) at object version level |
| `feed_versions` | Immutable snapshots of feed algorithms |
| `channels` | Producer outputs (separated from consumer feeds) |

### 2. Semantic Extraction Pipeline

| Component | What It Does |
|-----------|-------------|
| Heuristic classifier | Classifies tweets as theory/problem/observation/prediction/evidence_for/evidence_against |
| LLM compiler | Muse Spark 1.3 extracts typed objects + edges from tweets |
| Scoring formula | `alpha = (source_proximity × novelty × bottleneck_relevance × specificity × surprise) / (promotion + repetition + consensus_saturation + performative_posting)` |
| Source distance | 0=experimenter, 1=collaborator, 2=specialist, 3=analyst, 4=journalist, 5=influencer |
| Claim classification | 11 types: theory, observation, problem, prediction, evidence_for, evidence_against, entity, technology, decision, pick, question |

### 3. X Account Data Extraction

| Phase | Accounts | Tweets | August Data |
|-------|----------|--------|-------------|
| Phase 1: August | 102 | 2,384 | ✅ Full |
| Phase 2: July | 15 | 84 | ✅ Full |
| Phase 3: June | 15 | 85 | ✅ Full |
| **Total** | **101** | **2,553** | **33 with Aug** |

### 4. Knowledge Graph

| Metric | Count |
|--------|-------|
| Objects | 3,548 |
| Edges | 584 |
| Supports | 196 |
| Contradicts | 25 |
| Related_to | 359 |
| Predictions found | 258 |
| Predictions connected | 140 |

### 5. BEAR-Style Alpha Analysis

| Rank | Account | Alpha Score | Key Finding |
|------|---------|-------------|-------------|
| 1 | @danfei_xu | 5.5 | "No one building robots you can buy" |
| 2 | @ProfJohnARogers | 4.7 | Interface layer spawns research |
| 3 | @bravo_abad | 4.6 | "AI explores protein architectures evolution never tried" |
| 4 | @ZitongYang0 | 4.4 | Stanford PhD: self-improving AI |
| 5 | @YuchenXiao5 | 4.1 | Unitree insider |

---

## Files Created

### Core (modified)
- `feedify/models.py` — 7 tables
- `feedify/schemas.py` — ObjectDraft, EdgeDraft
- `feedify/services/detector.py` — Claim classification + scoring
- `feedify/services/ingestion.py` — Async LLM compilation
- `feedify/services/feeds.py` — Delta feeds
- `feedify/services/ranking.py` — Object scoring
- `feedify/services/minimal_graph.py` — DB-backed graph
- `feedify/services/frontier_graph.py` — Reads from DB
- `feedify/api.py` — 55 routes
- `feedify/mcp_server.py` — 11 tools

### New
- `feedify/services/llm_compiler.py` — Muse Spark integration
- `feedify/services/compiled_feed.py` — Multi-stage pipeline
- `feedify/services/embedding.py` — Semantic similarity
- `feedify/services/chatgpt_importer.py` — Conversation importer
- `feedify/services/recursive_expansion.py` — Account discovery
- `config/acceleration_watchlist.json` — 102 accounts with source_distance

### Documentation
- `specs/aithesis_people.md` — 100-account research graph
- `specs/x_account_registry.md` — Categorized accounts
- `specs/tweet_bank.md` — 2,553 raw tweets
- `specs/extraction_review.md` — How to avoid slop
- `specs/canonical-thesis-v2.md` — Scarcity migration thesis
- `specs/feedify_bear_integration.md` — Future integration plan
- `specs/august-data-plan.md` — Historical extraction protocol
- `august/analysis/full-analysis.md` — BEAR-style alpha analysis
- `august/analysis/backtest-results.md` — Prediction tracking
- `august/analysis/graph-analysis.md` — Graph connections

---

## DB State (Updated)

```
feedify2.db:
  artifacts: 2,553
  objects: 6,101
  edges: 3,622
  feeds: 6
  interactions: 0
  feed_versions: 0
  channels: 0
```

### Edge Types
- supports: 196
- contradicts: 25
- related_to: 359
- temporal: 1,760
- converges_with: 462
- embedding_similarity: 420

### Convergences Detected
- 88 multi-author convergences
- Sep 9, 2026: 6 thesis topics converged simultaneously
- Biology: 54 theories from 15 authors (strongest cluster)
- @nicole_delrosso: Top bottleneck/scarcity contributor
- @advaith_sridhar: Top materials/energy contributor

---

## What Works

1. ✅ Data model is correct (Artifact → Object → Edge)
2. ✅ Heuristic classifier works (theory/problem/observation/prediction)
3. ✅ Scoring formula filters low-alpha posts
4. ✅ Source distance models experimenter vs influencer
5. ✅ Delta feeds detect what changed
6. ✅ MCP tools work (11 tools)
7. ✅ All 41 tests pass
8. ✅ Service running on v2.feedify.egoic.ai
9. ✅ Graph has 584 edges connecting predictions to evidence
10. ✅ BEAR-style analysis identifies top alpha accounts

---

## What's Not Working Yet

1. ❌ LLM compiler not running on full dataset (tested on 1 tweet only)
2. ❌ No interaction tracking (DONE/SAVE/FOLLOW/NOISE)
3. ❌ No claim_lead_time automation
4. ❌ Edges are embedding-based but not temporal
5. ❌ No convergence detection wired into pipeline
6. ❌ No recursive expansion in production

---

## The Thesis (Canonical v2.0)

> **What does increasing abundance make newly scarce?**

AGI makes cognition abundant → verification becomes scarce → verification gets automated → physical experiments become scarce → instruments become scarce → manufacturing scales → energy/permissions become scarce.

**The master equation:**

$$
Alpha_i = \sum_{s,t} (P_{ours}(s,t) - P_{market}(s,t)) \times \Delta CF_i(s,t) \times X_i(s) \times B_i(s,t) \times R_i(t) - C_i(t)
$$

---

## Next Steps (Priority Order)

### Immediate (This Week)

1. **Run LLM compiler on top 50 high-value tweets** — Muse Spark extraction for the most important content
2. **Add temporal edges** — Track prediction date → evidence date → lead time
3. **Wire interaction tracking** — Enable DONE/SAVE/FOLLOW/NOISE on the API

### Short-term (Next Week)

4. **Build convergence detection** — When multiple source_distance=0 accounts discuss the same topic
5. **Selective 2-year extraction** — Top 5 accounts: @danfei_xu, @ProfJohnARogers, @bravo_abad, @ZitongYang0, @YuchenXiao5
6. **Backtest predictions** — Track the 10 high-value predictions listed in backtest-results.md

### Medium-term (This Month)

7. **Port BEAR's cursor pagination** — Fix the "accounts with 0 August tweets" problem
8. **Build the "AI→Atoms Index"** — Universe around test + measurement + characterization
9. **World-State Consistency Arbitrage** — Reverse-DCF thousands, find contradictory implied futures
10. **Deploy to production** — v2.feedify.egoic.ai with full LLM compilation

---

## Cost Summary

| Item | Cost |
|------|------|
| GetXAPI (2,553 tweets) | $0.13 |
| GetXAPI (84 July tweets) | $0.004 |
| GetXAPI (85 June tweets) | $0.004 |
| **Total API cost** | **$0.14** |
| LLM (Muse Spark 1.3 contributor) | ~$0.01 per 1K tokens |
| **Estimated full LLM compilation** | ~$0.50 for all 2,553 tweets |

---

## Key Insight from This Session

**The original feedify watchlist had higher-alpha accounts than the aithesis list.**

The aithesis list was curated for specific research areas. The original feedify watchlist was curated for signal density — accounts that consistently produce falsifiable claims.

The smart approach is not "extract everything" — it's "extract what produces alpha, then build the graph to connect predictions to evidence."

That's what BEAR does with crypto traders. We're now doing it with researchers.
