# Feedify 2.0

**Knowledge graph compiler for post-AGI scarcity intelligence.**

Feedify ingests X/Twitter posts from researchers and engineers, classifies them into typed knowledge objects, builds relationships between objects, and tracks predictions over time. The core thesis: "What does increasing abundance make newly scarce?"

```
cd /root/feedify2
source .venv/bin/activate
uvicorn feedify.api:app --reload --port 8788

# Quick test
curl http://localhost:8788/api/health
curl http://localhost:8788/api/convergence?days=30
curl http://localhost:8788/api/predictions?limit=5
```

## What's inside

| Module | Role |
|---|---|
| `feedify/adapters/` | 9 source adapters (X, GitHub, HN, SEC, OpenInsider, TrustMRR, StoreLeads, Appfigures, Glama) |
| `feedify/services/` | Core logic (25 files) — classification, scoring, convergence, graph building |
| `feedify/api.py` | FastAPI server (55+ routes) |
| `feedify/models.py` | 7 tables: artifacts, objects, edges, feeds, interactions, feed_versions, channels |
| `feedify/schemas.py` | Pydantic schemas for API |
| `august/` | Extracted tweet data (101 accounts, 3,357 tweets) |
| `specs/` | Analysis docs, thesis, account registry |
| `tests/` | 41 tests, all passing |

## Documentation

- [`AGENTS.md`](AGENTS.md) — binding rules for coding agents
- [`HANDOVER.md`](HANDOVER.md) — full project state
- [`NEXT_STEPS.md`](NEXT_STEPS.md) — what's done and what's next
- [`QUICKSTART.md`](QUICKSTART.md) — fresh agent entry point
- [`docs/RECIPES.md`](docs/RECIPES.md) — common tasks and patterns
- [`docs/MCP.md`](docs/MCP.md) — future MCP server design
- [`specs/canonical-thesis-v2.md`](specs/canonical-thesis-v2.md) — the master equation
- [`specs/aithesis_people.md`](specs/aithesis_people.md) — 100-account research graph

## One-click bring-up

```bash
git clone <this repo> && cd feedify2
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -q                       # 41 tests pass
uvicorn feedify.api:app --reload --port 8788
```

## Architecture

```
                    X/Twitter Posts
                         │
                         ▼
              ┌─────────────────────┐
              │   ADAPTERS (9)      │
              │   X, GitHub, HN...  │
              └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   ARTIFACTS         │
              │   (immutable inputs)│
              └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   SEMANTIC COMPILER │
              │   classify + extract│
              └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   OBJECTS           │
              │   (typed knowledge) │
              │   theory|problem|   │
              │   prediction|...    │
              └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   EDGES             │
              │   (relationships)   │
              │   supports|contradicts│
              │   temporal|converges│
              └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   DELTA FEEDS       │
              │   (what changed)    │
              └─────────────────────┘
```

## DB State

```
Artifacts: 3,357 (raw tweets)
Objects: 7,120 (typed knowledge)
Edges: 5,685 (relationships)
Companies: 18 (AI→Atoms interface layer)
Short candidates: 5 (technical half-life mismatch)
Contradictions: 3 (world-state inconsistency)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health |
| `/api/objects` | GET | List objects (filters: domain, kind) |
| `/api/objects/{id}` | GET | Object detail with edges |
| `/api/graph` | GET | Knowledge graph context |
| `/api/graph/stats` | GET | Graph statistics |
| `/api/convergence` | GET | Multi-author convergence detection |
| `/api/predictions` | GET | Predictions with connected evidence |
| `/api/interactions` | POST | Record user actions |
| `/api/feeds/{slug}/compiled` | GET | Multi-stage compiled feed |
| `/api/feeds/{slug}/delta` | GET | Delta feed |
| `/api/import/chatgpt` | POST | Import conversations |
| `/api/ingest` | POST | Trigger ingestion |

## Core thesis

> **What does increasing abundance make newly scarce?**

AGI makes cognition abundant → verification becomes scarce → verification gets automated → physical experiments become scarce → instruments become scarce → manufacturing scales → energy/permissions become scarce.

The master equation:

$$
Alpha_i = (P_{ours} - P_{market}) \times \Delta CF_i \times X_i \times B_i \times R_i - C_i
$$

See [`specs/canonical-thesis-v2.md`](specs/canonical-thesis-v2.md) for the full derivation.

## Cost

| Item | Cost |
|------|------|
| GetXAPI (3,357 tweets) | ~$0.17 |
| LLM (Muse Spark 1.3 contributor) | ~$0.01 per 1K tokens |
| **Total** | **~$0.18** |

## License

Proprietary. Do not distribute.
