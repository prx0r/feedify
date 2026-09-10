# Feedify v2 — AGENTS.md

**Repo**: github.com/prx0r/feedify (v2 code)
**Running**: v2.feedify.egoic.ai:8788
**Code**: /root/feedify2
**Status**: ACTIVE — develop here

---

## What This Is

Feedify v2 is a **knowledge graph compiler** that ingests X/Twitter posts, classifies them into typed knowledge objects, builds relationships, and tracks predictions over time.

**Architecture**: Artifacts → Objects → Edges → Delta Feeds

**Core thesis**: "What does increasing abundance make newly scarce?"

---

## Identity

I am the autonomous operator of Feedify 2.0. My job is to ingest X data from researchers, classify it into typed knowledge, build the relationship graph, and track predictions.

---

## The 10 Binding Rules

### Rule 1: Always Paginate GetXAPI
GetXAPI returns max 20 tweets per page. ALWAYS use cursor pagination.
```python
params = {"q": f"from:{handle} since:2026-08-01 until:2026-08-31", "count": 20, "cursor": cursor}
```

### Rule 2: Always Use Date Filters
`product=Latest` returns whatever's in the index, not specific months. ALWAYS use `since:YYYY-MM-DD until:YYYY-MM-DD`.

### Rule 3: Raw Before Filter
Store everything, filter during analysis. Never throw away a tweet.

### Rule 4: Source Distance Matters
0=experimenter, 1=collaborator, 2=specialist, 3=analyst, 4=journalist, 5=influencer. Score accordingly.

### Rule 5: Classify Claims
Not everything is a "claim". Use: theory, observation, problem, prediction, evidence_for, evidence_against.

### Rule 6: Track Predictions
Every prediction should have a backtest plan: what would prove it right/wrong, and when.

### Rule 7: Build Edges
Objects without edges are isolated. Connect: supports, contradicts, related_to, temporal, converges_with.

### Rule 8: Delta Feeds
The killer feature: "what changed since I last looked?" requires interaction tracking.

### Rule 9: Convergence Is Alpha
When multiple source_distance=0 accounts discuss the same topic, that's signal.

### Rule 10: Test Before Push
Run `pytest tests/ -q` before any push. 41 tests must pass.

---

## What Works

- FastAPI + SQLite (7 tables)
- 9 source adapters (same as v1)
- Claim classification (theory/problem/observation/prediction/evidence_for/evidence_against)
- Source distance modeling (0-5)
- Scoring formula (alpha = proximity × novelty × relevance × specificity × surprise / noise)
- Delta feeds (what changed since user last saw)
- Convergence detection (multi-author, same topic, same time)
- 584+ edges connecting predictions to evidence
- MCP server (11 tools)
- ChatGPT conversation importer
- LLM compiler (Muse Spark 1.3 contributor)
- 41 tests passing

---

## DB State

```
3,357 artifacts (tweets)
6,101 objects (typed knowledge)
3,622 edges (relationships)
1,043 August tweets from 37 accounts
```

---

## Open Threads

### High Priority
1. **LLM compiler on full dataset** — Tested on 1 tweet, needs full run on 50+ high-value tweets
2. **Wire interaction tracking** — Code exists, not wired into main pipeline
3. **Build convergence detection into ingestion** — Auto-detect when new posts create convergence

### Medium Priority
4. **Selective 2-year extraction** — Top 5 accounts: @danfei_xu, @ProfJohnARogers, @bravo_abad, @ZitongYang0, @YuchenXiao5
5. **Backtest predictions** — Track the 10 high-value predictions
6. **Temporal edge enrichment** — Track prediction date → evidence date → lead time

### Low Priority
7. **Port BEAR's cursor pagination** — For complete timeline extraction
8. **Build "AI→Atoms Index"** — Universe around test + measurement + characterization
9. **World-State Consistency Arbitrage** — Reverse-DCF thousands
10. **Deploy to production** — v2.feedify.egoic.ai with full LLM compilation

---

## How to Run

```bash
cd /root/feedify2
source .venv/bin/activate
pytest tests/ -q  # 41 tests
uvicorn feedify.api:app --reload --port 8788
```

---

## Key Files

| File | Purpose |
|------|---------|
| `HANDOVER.md` | Full project state |
| `QUICKSTART.md` | Fresh agent entry point |
| `SESSION_REVIEW.md` | Session timeline |
| `specs/canonical-thesis-v2.md` | The thesis |
| `specs/aithesis_people.md` | 100-account research graph |
| `august/HISTORICAL_PROTOCOL.md` | Extraction protocol (pagination lesson) |

---

## Do Not

- Do not develop in /root/feedify (v1, legacy)
- Do not push without running tests
- Do not use GetXAPI without pagination
- Do not use GetXAPI without date filters
- Do not commit .env files
- Do not break the running v2 service
