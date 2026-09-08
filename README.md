# Feedify Alpha MVP

Feedify is a **personal signal compiler**:

`Sources → normalized records → typed signals → user algorithms → feeds → web / iOS Home Screen / JSON / RSS / MCP / x402`

This repo is deliberately a single Python service with a zero-build web UI so a coding agent can run it immediately, then split services only when usage forces it.

## What works now

- FastAPI application + SQLite persistence.
- Polished responsive feed UI; no frontend build step.
- Prompt-defined feed algorithms with weights, filters, keywords, freshness and source-priority scoring.
- Feed creation, editing API, forking and public sharing.
- Per-feed PWA manifest + generated icon so individual feeds can be added to an iOS Home Screen under their own identity.
- JSON and RSS outputs for every public feed.
- Standalone Feedify MCP server with `list_feeds`, `get_feed`, `search_feed`.
- Generic remote MCP bridge for configured Streamable-HTTP servers.
- Optional x402 v2 paid route for machine-readable feeds.
- Real source adapters:
  - TrustMRR verified startup economics (API key)
  - Store Leads Shopify app/merchant intelligence (API key)
  - Appfigures estimates for configured app IDs (licensed API credentials)
  - Glama MCP directory (public)
  - GitHub repository acceleration (public; token optional)
  - Hacker News early builder launches (public)
- Deterministic signal detectors for `REVENUE_ACCELERATION`, `ACQUISITION_MISPRICING`, `NEW_CAPABILITY`, `REPO_ACCELERATION`, `TECH_ADOPTION`, `APP_BREAKOUT`, `EARLY_BUILDER_SIGNAL`, and `PLATFORM_CHANGE`.
- Optional OpenAI-compatible enrichment hook for OpenRouter / DeepSeek / similar providers.
- Seeded demo signals and five feeds matching the intended product thesis.

## 60-second start

```bash
cp .env.example .env
uv sync
uv run python -m feedify.cli seed
uv run uvicorn feedify.api:app --reload --port 8000
```

Open `http://localhost:8000`.

No paid API keys are required to boot the product. Public adapters can then be refreshed from the UI or CLI.

```bash
uv run python -m feedify.cli ingest github hackernews glama --limit 20
```

## Credentials

Add only what you have to `.env`:

```dotenv
TRUSTMRR_API_KEY=tmrr_...
STORELEADS_API_KEY=...
GITHUB_TOKEN=github_pat_...
APPFIGURES_USERNAME=...
APPFIGURES_PASSWORD=...
APPFIGURES_CLIENT_KEY=...
APPFIGURES_PRODUCT_IDS=123,456
APIFY_TOKEN=apify_api_...
```

TrustMRR, Store Leads, and Apify expose remote MCP surfaces. With the MCP extra installed, Feedify can introspect/call Streamable-HTTP MCP servers:

```bash
uv sync --extra mcp
```

Feedify automatically registers sensible MCP presets:

- TrustMRR: authenticated endpoint when `TRUSTMRR_API_KEY` exists; otherwise its bounded discovery endpoint.
- Store Leads: authenticated endpoint when `STORELEADS_API_KEY` exists.
- Apify: authenticated endpoint when `APIFY_TOKEN` exists; otherwise anonymous Actor/docs discovery tools.

Add arbitrary remote MCPs via `MCP_SOURCES_JSON`.

## Feed algorithm model

A feed stores:

- `prompt`: human definition of desired attention.
- `weights`: importance of novelty/actionability/source proximity/confidence/evidence/freshness.
- `filters`: domains, signal types, include/exclude terms, source priority, freshness decay, minimum score.
- `icon`, name and public/share state.

Feed scoring is intentionally transparent and inspectable. A future LLM can propose or evolve the algorithm, but deterministic weights own the final ranking.

Example feed prompt:

> Only show me newly buildable commerce opportunities from obscure primary-source engineers, new MCPs/APIs and verified market data. Suppress generic AI commentary and anything I cannot ship against.

The heuristic compiler raises novelty/actionability/source-proximity weights and sets a stricter minimum score. The API lets a coding agent replace those values directly.

## iOS "feed apps"

Open any feed in Safari, e.g. `/f/agent-commerce-alpha`, then use **Share → Add to Home Screen**. Feedify emits a feed-specific web manifest, `apple-mobile-web-app-title`, and generated icons. Each feed therefore gets a distinct launcher while sharing one underlying engine.

This is separate from a future native Feedify client; the backend contracts are already suitable for one.

## Machine outputs

For `agent-commerce-alpha`:

```text
GET /api/feeds/agent-commerce-alpha.json
GET /api/feeds/agent-commerce-alpha.rss
GET /api/paid/feeds/agent-commerce-alpha.json
```

The `/paid/` route is identical until x402 is enabled.

### MCP

```bash
uv sync --extra mcp
uv run feedify-mcp
```

Example Claude/Cursor configuration can point at the stdio command. The MCP server exposes public feeds as agent tools.

### x402

See `docs/X402.md`. For a safe first run, use Base Sepolia and the public testnet facilitator. Do not put a mainnet wallet private key into this repo.

## Tests

```bash
uv run pytest -q
```

The test suite covers algorithm inference, signal detection, DB/feed ranking, API creation/export and iOS manifest/icon endpoints.

## Repo map

```text
feedify/
  adapters/             upstream data integrations
  services/
    detector.py         source record -> typed signals
    ingestion.py        idempotent persistence
    ranking.py          deterministic personal algorithms
    feeds.py            ranking + JSON/RSS/icon/manifest output
    mcp_remote.py       remote MCP bridge
    llm.py              optional OpenAI-compatible enrichment
  api.py                product API + static UI
  mcp_server.py         Feedify as an MCP server
  x402.py               optional payment middleware
static/                  no-build responsive web app
tests/                   regression suite
config/                  source/watchlist catalogs
docs/                    coding-agent handoff
```

## Product rule

Do **not** turn Feedify into another generic social reader. Every new feature should improve one of:

1. source exclusivity,
2. signal extraction,
3. personal ranking quality,
4. cross-source corroboration,
5. actionability,
6. low-noise delivery,
7. portability/monetization of a user's algorithm.

The core product object is the **feed algorithm**, not the post.
