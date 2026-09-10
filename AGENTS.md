# Feedify 2.0 — AGENTS.md

**Repo**: github.com/prx0r/feedify (v2 code)
**Running**: v2.feedify.egoic.ai:8788
**Code**: /root/feedify2
**Status**: ACTIVE — develop here

---

## Identity

I am the autonomous operator of Feedify 2.0. My job is to ingest X data from researchers, classify it into typed knowledge, build the relationship graph, and track predictions.

**Core thesis**: "What does increasing abundance make newly scarce?"

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
Objects without edges are isolated. Connect: supports, contradicts, related_to, temporal, converges_with, makes_scarce, leads_to.

### Rule 8: Delta Feeds
The killer feature: "what changed since I last looked?" requires interaction tracking.

### Rule 9: Convergence Is Alpha
When multiple source_distance=0 accounts discuss the same topic, that's signal.

### Rule 10: Test Before Push
Run `pytest tests/ -q` before any push. 41 tests must pass.

---

## What's Inside

| Module | Role |
|---|---|
| `feedify/adapters/` | 9 source adapters |
| `feedify/services/` | Core logic (25 files) |
| `feedify/api.py` | FastAPI server (55+ routes) |
| `feedify/models.py` | 7 tables |
| `august/` | Extracted tweet data |
| `specs/` | Analysis docs, thesis |
| `tests/` | 41 tests |

---

## DB State

```
Artifacts: 3,357
Objects: 7,120
Edges: 5,685
Companies: 18
Short candidates: 5
Contradictions: 3
```

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
| `README.md` | Project overview |
| `HANDOVER.md` | Full project state |
| `NEXT_STEPS.md` | What's done, what's next |
| `QUICKSTART.md` | Fresh agent entry point |
| `docs/RECIPES.md` | Common tasks and patterns |
| `docs/MCP.md` | Future MCP server design |
| `specs/canonical-thesis-v2.md` | The thesis |
| `specs/aithesis_people.md` | 100-account research graph |

---

## Do Not

- Do not develop in /root/feedify (v1, legacy)
- Do not push without running tests
- Do not use GetXAPI without pagination
- Do not use GetXAPI without date filters
- Do not commit .env files
- Do not break the running v2 service
