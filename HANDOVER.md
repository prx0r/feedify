# Feedify 2.0 — Agent Handover

**Created**: 2026-09-10
**Purpose**: Bring a fresh agent up to speed on everything

---

## What Is Feedify?

Feedify is a **knowledge graph compiler** that ingests X/Twitter posts from researchers and engineers, classifies them into typed knowledge objects, builds relationships between objects, and tracks predictions over time.

**Core thesis**: "What does increasing abundance make newly scarce?"

**The master equation**:
$$Alpha_i = (P_{ours} - P_{market}) \times \Delta CF_i \times X_i \times B_i \times R_i - C_i$$

---

## What's Running

| Service | URL | Port | Code Location |
|---------|-----|------|---------------|
| Feedify v1 (original) | feedify.egoic.ai | 8787 | /root/feedify |
| Feedify v2 (rewrite) | v2.feedify.egoic.ai | 8788 | /root/feedify2 |

**The GitHub repo (prx0r/feedify) currently contains the v2 code** (pushed 2026-09-10). The v1 code still runs on the server but is not in the repo anymore.

---

## Current DB State

```
feedify2.db:
  artifacts: 2,553 (raw tweets)
  objects: 6,101 (typed knowledge)
  edges: 3,622 (relationships)
  feeds: 6
  interactions: 0
```

### Edge Types
| Type | Count | Purpose |
|------|-------|---------|
| supports | 196 | Evidence supporting a prediction |
| contradicts | 25 | Evidence contradicting a prediction |
| related_to | 359 | Same topic, same author |
| temporal | 1,760 | Same author, different dates, same topic |
| converges_with | 462 | Different authors, same topic, same time |
| embedding_similarity | 420 | Semantic similarity between objects |

---

## X Account Extraction Status

### What's Been Extracted

| Phase | Accounts | Tweets | Months | Status |
|-------|----------|--------|--------|--------|
| Phase 1: August | 102 | 2,384 | Aug 2026 | ✅ Complete |
| Phase 2: July | 15 | 84 | Jul 2026 | ✅ Complete |
| Phase 3: June | 15 | 85 | Jun 2026 | ✅ Complete |
| **Total** | **101** | **2,553** | **Aug+Jul+Jun** | |

### Account Coverage

| Status | Count | Notes |
|--------|-------|-------|
| Full August (10+ tweets) | 9 | @GenAI_is_real (24), @AnnaCiaunica (22), etc. |
| Partial August (1-9 tweets) | 25 | Mix of sparse posters |
| No August, has other data | 68 | Researchers who didn't tweet Aug |
| No data at all | 1 | @theaustinlyons |

**Key finding**: 68 accounts simply didn't tweet in August 2026. GetXAPI index is fine — these were on summer break or writing papers.

### Top Alpha Accounts (BEAR-style scoring)

| Rank | Handle | Alpha | Domain | Key Finding |
|------|--------|-------|--------|-------------|
| 1 | @danfei_xu | 5.5 | robotics | "No one building robots you can buy" |
| 2 | @ProfJohnARogers | 4.7 | bio-electronics | Interface layer spawns research |
| 3 | @bravo_abad | 4.6 | autonomous-science | "AI explores protein architectures evolution never tried" |
| 4 | @ZitongYang0 | 4.4 | self-improving | Stanford PhD: self-improving AI |
| 5 | @YuchenXiao5 | 4.1 | robotics | Unitree insider |

---

## Data Model (v2)

### Tables

| Table | Purpose |
|-------|---------|
| `artifacts` | Immutable inputs (tweets) — replaces `source_records` |
| `objects` | Versioned knowledge (theories, problems, predictions) — replaces `signals` |
| `edges` | Relationships (supports, contradicts, related_to, temporal, converges_with) |
| `feeds` | Versioned attention programs |
| `interactions` | User actions (DONE/SAVE/FOLLOW/NOISE) |
| `feed_versions` | Immutable snapshots of feed algorithms |
| `channels` | Producer outputs |

### Object Kinds

| Kind | Count | What It Means |
|------|-------|---------------|
| claim | 1,200+ | Generic (needs LLM to classify properly) |
| theory | 54+ | Causal claim about how something works |
| problem | 26+ | Something broken or suboptimal |
| observation | 53+ | Empirical report of what was seen |
| prediction | 397 | Claim about what will happen |
| evidence_for | 11+ | Data supporting a theory |
| evidence_against | 15+ | Data contradicting a theory |

### Scoring Formula

$$alpha = \frac{source\_proximity \times novelty \times bottleneck\_relevance \times specificity \times surprise}{promotion + repetition + consensus\_saturation + performative\_posting + 0.1}$$

Posts below 0.15 alpha are filtered out.

### Source Distance

| Distance | Label | What It Means |
|----------|-------|---------------|
| 0 | Experimenter | Running experiments / designing chips |
| 1 | Collaborator | Immediate team |
| 2 | Specialist | Observing field |
| 3 | Analyst | Interprets others' work |
| 4 | Journalist | Reports on field |
| 5 | Influencer | Engagement-first |

---

## What's In the Repo

```
feedify2/
├── config/              # 5 watchlist files (102 accounts with source_distance)
├── data/                # Events, raw data, theses
├── docs/                # Architecture, vision, build notes
├── feedify/             # Python package
│   ├── adapters/        # X, GitHub, HN, SEC, etc. (9 adapters)
│   ├── services/        # 25 service files
│   │   ├── llm_compiler.py     # Muse Spark 1.3 integration
│   │   ├── compiled_feed.py    # Multi-stage feed pipeline
│   │   ├── embedding.py        # Semantic similarity
│   │   ├── chatgpt_importer.py # Conversation importer
│   │   └── recursive_expansion.py # Account discovery
│   ├── api.py           # 55 routes
│   ├── models.py        # 7 tables
│   └── schemas.py       # ObjectDraft, EdgeDraft
├── specs/               # Active specs (8 files)
├── august/              # Extraction data
│   ├── prima_materia/   # 101 JSON files with raw tweets
│   ├── analysis/        # Alpha, backtest, convergence reports
│   └── categories/      # Domain reports
├── tests/               # 41 tests, all passing
└── feedify2.db          # SQLite database
```

---

## Key Specs

| File | What It Contains |
|------|-----------------|
| `specs/canonical-thesis-v2.md` | The master equation and scarcity migration thesis |
| `specs/aithesis_people.md` | 100-account research graph with source_distance |
| `specs/x_account_registry.md` | All 102 accounts categorized by domain |
| `specs/tweet_bank.md` | All 2,553 tweets grouped by account |
| `specs/extraction_review.md` | How to avoid slop in extraction |
| `specs/feedify_bear_integration.md` | Future integration with BEAR repo |

---

## Key Findings

### 1. Sep 9 Convergence
6 thesis topics converged simultaneously across 15+ authors on September 9, 2026. Worth investigating what event triggered this.

### 2. Biology Is Strongest Cluster
54 theories from 15 authors. @nicole_delrosso is the top contributor to bottleneck/scarcity theories.

### 3. Original Feedify Watchlist Had Higher Alpha
The aithesis list was curated for specific research areas. The original feedify watchlist was curated for signal density — accounts that consistently produce falsifiable claims.

### 4. Predictions Have 3-12 Month Lead Times
The predictions that DO have connected evidence show 3-12 months between prediction and mainstream recognition.

---

## What's NOT Working Yet

1. **LLM compiler not on full dataset** — Tested on 1 tweet, needs full run
2. **No interaction tracking in production** — Code exists, not wired
3. **Edges are embedding-based but not temporal enough** — Need more semantic similarity
4. **No convergence detection in production** — Code exists, not wired
5. **68 accounts have no August data** — They didn't tweet, not an extraction failure

---

## Next Steps

### Immediate
1. Run LLM compiler on top 50 high-value tweets
2. Wire interaction tracking into the API
3. Build convergence detection into the pipeline

### Short-term
4. Selective 2-year extraction for top 5 accounts
5. Backtest the 10 high-value predictions
6. Deploy v2 to production

### Medium-term
7. Port BEAR's cursor pagination for complete timelines
8. Build "AI→Atoms Index" — universe around test + measurement
9. World-State Consistency Arbitrage — reverse-DCF thousands

---

## How to Run

```bash
cd /root/feedify2
source .venv/bin/activate

# Run tests
pytest tests/ -q

# Start server
uvicorn feedify.api:app --reload --port 8788

# Check health
curl http://localhost:8788/api/health
```

---

## Cost Summary

| Item | Cost |
|------|------|
| GetXAPI (2,553 tweets) | $0.14 |
| LLM (Muse Spark 1.3 contributor) | ~$0.01 per 1K tokens |
| **Total so far** | **~$0.15** |

---

## Important Notes

1. **The GitHub repo has v2 code only** — v1 was overwritten by push on 2026-09-10
2. **Both services still run** — v1 on port 8787, v2 on port 8788
3. **GetXAPI index has gaps** — Some accounts have no August data because they didn't tweet
4. **LLM API key is in .env** — Don't commit it
5. **41 tests pass** — Run `pytest tests/ -q` to verify
