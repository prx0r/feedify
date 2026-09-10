# Feedify 2.0 — Agent Handover

**Created**: 2026-09-10
**Purpose**: Bring a fresh agent up to speed on everything
**Status**: Working — v2 deployed at v2.feedify.egoic.ai

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

**The GitHub repo (prx0r/feedify) contains the v2 code.**

---

## Current DB State

```
feedify2.db:
  artifacts: 3,357 (raw tweets)
  objects: 7,046 (typed knowledge)
  edges: 5,207 (relationships)
  feeds: 6
  interactions: 0
```

### Object Kinds
| Kind | Count | What It Means |
|------|-------|---------------|
| claim | 5,135 | Generic (needs LLM to classify properly) |
| observation | 729 | Empirical report of what was seen |
| theory | 388 | Causal claim about how something works |
| prediction | 343 | Claim about what will happen |
| problem | 291 | Something broken or suboptimal |
| person | 96 | Account entities with source_distance |
| evidence_against | 26 | Data contradicting a theory |
| evidence_for | 25 | Data supporting a theory |

### Edge Types
| Type | Count | Purpose |
|------|-------|---------|
| temporal | 1,783 | Same author, different dates, same topic |
| supports | 1,571 | Evidence supporting a prediction |
| converges_with | 967 | Different authors, same topic, same time |
| related_to | 857 | Same topic, same author |
| contradicts | 25 | Evidence contradicting a prediction |

### Convergences
- 145 multi-author convergences detected
- Sep 9, 2026: 6 thesis topics converged simultaneously
- Aug 10, 2026: Materials convergence (14 posts, 14 experimenters)

### Predictions
- 343 predictions tracked
- 109 with connected evidence

---

## X Account Extraction Status

### What's Been Extracted

| Phase | Accounts | Tweets | August Data |
|-------|----------|--------|-------------|
| Phase 1: August (paginated) | 102 | 3,076 | ✅ 1,043 tweets from 37 accounts |
| Phase 2: July | 15 | 84 | ✅ Complete |
| Phase 3: June | 15 | 85 | ✅ Complete |
| **Total** | **101** | **3,357** | **1,043 August tweets** |

### August Coverage (Corrected with Pagination)

| Account | August | Total | Domain |
|---------|--------|-------|--------|
| @aleabitoreddit | 197 | 233 | stocks |
| @DeepDishEnjoyer | 194 | 200 | stocks |
| @arthurcolle | 174 | 199 | ai-research |
| @GenAI_is_real | 106 | 133 | ai-research |
| @bravo_abad | 76 | 113 | autonomous-science |
| @AnnaCiaunica | 55 | 55 | cognition |
| @jxmnop | 49 | 106 | ai-research |
| @tengyanAI | 33 | 49 | hardware |
| @ryancjulian | 27 | 81 | robotics |
| @advaith_sridhar | 23 | 57 | materials |

**17 accounts active all 3 months** (Aug+Jul+Jun) — these are the core research graph.

---

## Data Model (v2)

### Tables

| Table | Purpose |
|-------|---------|
| `artifacts` | Immutable inputs (tweets) |
| `objects` | Versioned knowledge (theories, problems, predictions) |
| `edges` | Relationships (supports, contradicts, related_to, temporal, converges_with) |
| `feeds` | Versioned attention programs |
| `interactions` | User actions (DONE/SAVE/FOLLOW/NOISE) |
| `feed_versions` | Immutable snapshots of feed algorithms |
| `channels` | Producer outputs |

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

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | System health |
| `GET /api/objects` | List objects (filters: domain, kind) |
| `GET /api/objects/{id}` | Object detail with edges |
| `GET /api/graph` | Knowledge graph context |
| `GET /api/graph/stats` | Graph statistics |
| `GET /api/convergence` | Multi-author convergence detection |
| `GET /api/predictions` | Predictions with connected evidence |
| `POST /api/interactions` | Record user actions |
| `GET /api/feeds/{slug}/compiled` | Multi-stage compiled feed |
| `GET /api/feeds/{slug}/delta` | Delta feed (what changed) |
| `POST /api/import/chatgpt` | Import conversations |
| `POST /api/ingest` | Trigger ingestion |

---

## What's In the Repo

```
feedify2/
├── config/              # 5 watchlist files (102 accounts)
├── data/                # Events, raw data, theses
├── docs/                # Architecture, vision, build notes
├── feedify/             # Python package
│   ├── adapters/        # X, GitHub, HN, SEC, etc. (9 adapters)
│   ├── services/        # 25 service files
│   ├── api.py           # 55+ routes
│   ├── models.py        # 7 tables
│   └── schemas.py       # ObjectDraft, EdgeDraft
├── specs/               # Active specs (8 files)
├── august/              # Extraction data
│   ├── prima_materia/   # 101 JSON files with raw tweets
│   ├── analysis/        # Alpha, backtest, convergence reports
│   └── categories/      # Domain reports
├── tests/               # 41 tests, all passing
├── HANDOVER.md          # This file
├── SESSION_REVIEW.md    # Session summary
└── feedify2.db          # SQLite database
```

---

## Key Specs

| File | What It Contains |
|------|-----------------|
| `specs/canonical-thesis-v2.md` | The master equation and scarcity migration thesis |
| `specs/aithesis_people.md` | 100-account research graph with source_distance |
| `specs/x_account_registry.md` | All 102 accounts categorized by domain |
| `specs/tweet_bank.md` | All 3,357 tweets grouped by account |
| `specs/extraction_review.md` | How to avoid slop in extraction |
| `specs/feedify_bear_integration.md` | Future integration with BEAR repo |

---

## Key Findings

### 1. Sep 9 Convergence
6 thesis topics converged simultaneously across 15+ authors on September 9, 2026.

### 2. Biology Is Strongest Cluster
54 theories from 15 authors. @nicole_delrosso is the top contributor.

### 3. Original Feedify Watchlist Had Higher Alpha
The aithesis list was curated for specific research areas. The original feedify watchlist was curated for signal density.

### 4. Predictions Have 3-12 Month Lead Times
Validated predictions show 3-12 months between prediction and mainstream recognition.

---

## CRITICAL LESSON: Extraction Bugs

**GetXAPI returns max 20 tweets per page.** Without pagination and date filters, you get incomplete data.

**Correct extraction pattern:**
```python
params = {
    "q": f"from:{handle} since:2026-08-01 until:2026-08-31",
    "product": "Latest",
    "count": 20,
    "cursor": cursor,  # paginate with this
}
```

**Without pagination:**
- @GenAI_is_real: 24 August tweets (actual: 106)
- @DeepDishEnjoyer: 23 August tweets (actual: 194)

**With pagination (10 pages max):**
- @aleabitoreddit: 197 August tweets
- @DeepDishEnjoyer: 194 August tweets
- @arthurcolle: 174 August tweets

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
| GetXAPI (3,357 tweets) | ~$0.17 |
| LLM (Muse Spark 1.3 contributor) | ~$0.01 per 1K tokens |
| **Total so far** | **~$0.18** |

---

## Next Steps

1. Run LLM compiler on top 50 high-value tweets
2. Wire interaction tracking into the API
3. Build convergence detection into the pipeline
4. Selective 2-year extraction for top 5 accounts
5. Deploy v2 to production

---

## Important Notes

1. **The GitHub repo has v2 code only** — v1 was overwritten by push on 2026-09-10
2. **Both services still run** — v1 on port 8787, v2 on port 8788
3. **Always paginate GetXAPI** — max 20 tweets per page
4. **Always use date filters** — `since:YYYY-MM-DD until:YYYY-MM-DD`
5. **LLM API key is in .env** — Don't commit it
6. **41 tests pass** — Run `pytest tests/ -q` to verify
