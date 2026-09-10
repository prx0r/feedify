# Coding Agent Handoff

## Mission

Take this working MVP to a production-grade Feedify without changing the thesis:

> users design/share algorithms for attention; Feedify compiles heterogeneous sources into high-signal feeds and machine-readable products.

The user is especially interested in iOS app opportunities, App Store/meta distribution, SEO/search internals, agentic commerce, marketplace arbitrage, high-signal engineers/PMs, GitHub primitives and proprietary economic datasets.

## First commands

```bash
cp .env.example .env
uv sync --extra dev
uv run pytest -q
uv run uvicorn feedify.api:app --reload --port 8000
```

Do not begin a rewrite until the tests pass and you have used the seeded UI.

## Architecture decisions to preserve

### 1. Normalize before ranking
Every source adapter returns `NormalizedItem`. Do not make feed-specific adapters. Signal detectors convert upstream schemas into a small stable vocabulary.

### 2. Deterministic ranker owns delivery
LLMs can enrich, extract, recommend algorithms and explain signals. They should not be the only ranking mechanism. We need reproducibility, backtesting and user-forkable algorithms.

### 3. Keep raw evidence
`SourceRecord.raw` and `metrics` remain available for future reprocessing. Never discard the evidence used to create a signal.

### 4. Idempotent ingestion
`source_type + external_id` is unique. Re-ingestion refreshes metrics and detectors rather than duplicating items.

### 5. Source policy
Use official/public APIs or licensed access where possible. Respect TrustMRR's API terms: derive personal signals; do not reproduce its database. Do not add brittle scraping where a first-party API/MCP exists.

## Highest-priority production work

### P0 — real source coverage
Implement these as first-class adapters or reusable MCP recipes:

1. **Apify Store** — detect newly added/accelerating Actors; use its MCP server for actor discovery/execution.
2. **X high-signal graph** — ingest posts + replies from curated employees/builders; track reply-specific signal separately. Use a licensed X provider or configured Apify Actor, not unauthenticated scraping.
3. **Shopify developer/changelog + UCP/WebMCP sources** via RSS/GitHub.
4. **Stripe/x402/MPP project feeds** via RSS/GitHub/X.
5. **RevenueCat reports** as category-level economics priors.
6. **Meta/TikTok/Google ad intelligence** using compliant provider/API access; calculate advertiser persistence rather than merely showing creatives.
7. **Search/SEO primary sources**: Bing/Google engineers, Search Central changelogs, W3C/WICG proposals.
8. **Marketplace data**: eBay seller/product research where account/API terms permit; Etsy Marketplace Insights via user-authorized access if available.

### P0 — cross-source entity graph
Add stable entities:

- `Person`
- `Company`
- `Product/App`
- `Repository`
- `Protocol/Capability`
- `MarketplaceListing`
- `Merchant`

Add `EntityAlias` and `EvidenceEdge`.

This enables the real product:

`new MCP` + `GitHub acceleration` + `engineer reply` + `verified merchant demand` → one opportunity card.

### P0 — cross-source derived signals
Add detectors:

- `UNDERFOLLOWED_EXPERT`
- `INSIDER_DISCLOSURE`
- `REPLY_ALPHA`
- `AD_PERSISTENCE`
- `MARKETPLACE_SPREAD`
- `SEARCH_ACCELERATION`
- `MERCHANT_ADOPTION_ACCELERATION`
- `CAPABILITY_CONVERGENCE`
- `REVENUE_TO_AUDIENCE_ANOMALY`
- `BUILDABLE_OPPORTUNITY`

`BUILDABLE_OPPORTUNITY` should be a derived signal over evidence from at least two independent source families whenever possible.

### P1 — user accounts + syncing
Add auth and per-user ownership. Suggested stack: Postgres + SQLAlchemy/Alembic; auth provider can be added behind FastAPI. Keep public feed slugs separate from account identity.

### P1 — native iOS client
Backend already provides required contracts. Native client should support:

- feed creation by prompt,
- swipe/scroll feed,
- per-feed notification threshold,
- fork/share,
- widgets,
- deep links,
- alternate Feedify app icons,
- native share extension for adding an item/source to a feed,
- later: user-selected X/RSS/GitHub/source subscriptions.

Do not try to dynamically rename the native bundle. Preserve the PWA/per-feed Home Screen launcher path for arbitrary names/icons.

### P1 — notifications
Notifications are generated from a feed threshold, not raw source arrival. Add `delivery_threshold`, quiet hours and dedupe. A user should be able to say "notify me only above 0.91".

### P1 — backtesting
Persist every rank decision:

`feed_version`, `signal_id`, `score`, `rank`, `delivered_at`, `opened`, `saved`, `shared`, `dismissed`.

Then compare algorithm forks and optimize against explicit user actions. Never silently optimize purely for time spent.

### P2 — monetization
A public feed can opt into:

- free web/RSS/JSON,
- paid x402 JSON,
- paid MCP tool,
- paid email/push tier.

Take a platform fee on third-party paid feeds later. Keep source licensing constraints attached to each signal so a user cannot republish restricted underlying data.

## Suggested schema migration

Move from SQLite to Postgres only after P0 source/entity work. Add Alembic before migration. Tables:

- users
- feeds
- feed_versions
- source_configs
- source_records
- entities
- entity_aliases
- evidence_edges
- signals
- signal_evidence
- rank_events
- delivery_events
- feed_subscriptions
- source_licenses

## API contracts to preserve

Current routes are a useful v0 contract:

- `GET/POST /api/feeds`
- `GET /api/feeds/{slug}`
- `GET /api/feeds/{slug}.json`
- `GET /api/feeds/{slug}.rss`
- `POST /api/feeds/{slug}/fork`
- `POST /api/ingest`
- `GET /api/sources`
- `GET /api/mcp/{name}/tools`
- `POST /api/mcp/{name}/call`

Version them under `/v1` before public release; keep redirects for old clients.

## Signal scoring

Current score is intentionally simple. Evolve toward:

`P(relevant) × novelty × actionability × source proximity × evidence strength × exclusivity × freshness`

Then add diversity/novelty constraints at the feed level. Do not show five near-identical posts about the same launch.

### Source-specific reliability
Maintain source priors. Example:

- official engineer / protocol commit: high proximity
- proprietary transaction/revenue dataset: high evidence
- independent builder launch: high novelty, medium evidence
- generic commentary account: low proximity

### Hidden expert score

`authority × domain relevance × exclusivity × technical specificity × reply usefulness ÷ audience saturation`

Follower count should be used carefully: the goal is underpriced expertise, not obscurity for its own sake.

## Testing expectations

Before every substantial change:

1. run unit/API tests,
2. add fixture coverage for each external source schema,
3. test 429/retry behavior,
4. test source schema drift,
5. ensure one broken source cannot fail the entire ingestion sweep,
6. test idempotency,
7. test feed ranking determinism,
8. test RSS validity,
9. test PWA manifest/icon endpoints,
10. never test x402 using a wallet containing meaningful funds.

## Security

- API keys only through env/secret manager.
- Never persist OAuth tokens unencrypted.
- Remote MCP calls are potentially privileged; whitelist servers/tools per user and label read/write capabilities.
- Do not auto-run arbitrary Apify Actors or MCP tools without policy checks.
- Keep x402 payee/signer configuration separate; this repo should never hold a private key.
- Add SSRF protections before letting users register arbitrary source URLs.

## Definition of "done" for the next iteration

A strong next build should let a new user:

1. sign in,
2. type "obscure people building agent commerce primitives; only genuinely buildable alpha",
3. get a seeded algorithm,
4. connect/select real sources,
5. see a feed with evidence-backed opportunity cards,
6. fork someone else's algorithm,
7. share/install the feed on iOS,
8. expose it as RSS/JSON/MCP,
9. optionally monetize the machine endpoint,
10. receive only threshold-passing push alerts.
