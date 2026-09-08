# Feedify.dev — programmable feeds → products

**Feedify compiles a stream of information once, then turns it into many products.**

A Feedify feed is a versioned signal program with sources, ranking/generation logic, immutable items, provenance, subscribers, and a product chain. The same feed can be consumed in the mobile app, exported as RSS/JSON Feed, published by an X bot, delivered to a webhook, compiled into a blog/report, exposed to agents over MCP, or sold to machines through x402.

This is the advanced MVP (0.2). It extends the original Filterfeed/Feedify MVP rather than rebuilding it: the original feed engine, social model, RSS/JSON outputs and mobile app remain the core; the new product-chain layer sits on top.

## Product thesis

```text
SOURCE GRAPH                      PRODUCT GRAPH

X search ─────┐                   ┌─ Feedify social feed
GitHub ───────┤                   ├─ public web
RSS/Atom ─────┤                   ├─ RSS 2.0
JSON API ─────┼─> FEED PROGRAM ──┼─ JSON Feed 1.1
URLs ─────────┤   + memory        ├─ X bot / smart repost
Corpus/PDF ───┘   + provenance    ├─ webhook
                                  ├─ blog
                                  ├─ report
                                  ├─ MCP
                                  └─ x402 paid API
```

The important rule is **no output gets its own feed logic**. X bots, reports, paid endpoints and agents all read the same immutable `FeedItem` objects and provenance. That is what makes Feedify infrastructure rather than a collection of bots.

## What is implemented

### Feed engine
- `curate`, `distill`, `synthesize`, `generate` modes
- relevance / novelty / quality / actionability scoring
- immutable feed items with provenance
- natural-language FeedProgram compiler with deterministic fallback
- RSS/Atom ingestion
- URL ingestion
- GetXAPI X advanced-search ingestion
- GitHub repository search ingestion
- generic JSON API ingestion
- bounded corpus feeds for source-grounded synthetic/distilled streams

### Social app
- Expo SDK 57 / React Native mobile app
- Home, Explore, Create and Profile
- feed subscriptions
- reposts and feedback
- feed detail page
- new **Products** screen visualizing a feed's output chain
- one-tap creation of X bot, x402, webhook, blog and report outputs
- demo mode if the API is unavailable

### Product chain
Every feed automatically gets native Feedify, public web, RSS, JSON Feed and MCP outputs. Creators can attach additional outputs without changing the underlying feed.

Output catalog:
- `feedify`
- `public_web`
- `rss`
- `json_feed`
- `x_bot`
- `webhook`
- `blog`
- `report`
- `x402`
- `mcp`

Useful endpoints:

```text
GET  /v1/products/catalog
GET  /v1/feeds/:id/products
POST /v1/feeds/:id/products
POST /v1/feeds/:id/products/:outputId/publish
GET  /v1/feeds/:id/deliveries
GET  /v1/feeds/:id/manifest
GET  /v1/feeds/:id/chain
GET  /v1/feeds/:id/latest
```

A machine-readable feed manifest is also available at:

```text
GET /f/:slug/manifest.json
```

### X bot wiring
X publishing is an output, not part of the feed engine.

`strategy` supports:
- `post` — publish Feedify text as a new X post
- `quote` — quote the original X source when its post id is available
- `repost` — repost the original source item
- `smart` — source item → repost; transformed items → normal post with provenance. Set `allowQuote: true` only on an X plan that supports quote-post creation

X outputs default to `dryRun: true` in the demo. Set `X_USER_ACCESS_TOKEN` and `X_USER_ID`, then disable dry run on the output to go live.

### x402 paid feed wiring
`apps/x402-gateway` uses the official x402 Foundation TypeScript packages rather than a home-grown 402 implementation.

Each feed with an enabled `x402` output becomes a protected route such as:

```text
GET https://api.feedify.dev/paid/shopify-alpha/latest
```

Per-feed output config can specify:

```json
{
  "price": "$0.01",
  "network": "eip155:8453",
  "payTo": "0x..."
}
```

The gateway discovers enabled paid feeds from the Feedify API on startup, builds the x402 route map, verifies/settles through a facilitator, then serves the canonical Feedify item after payment. This means the paid API never has a second copy of ranking logic.

### MCP agent wiring
`apps/mcp-gateway` uses the current MCP v2 packages and exposes Feedify as agent tools:
- `list_feeds`
- `get_feed`
- `latest_signal`
- `feed_manifest`

The MCP gateway calls the shared `@feedify/sdk`, exactly like the x402 gateway.

### Feedify SDK
`packages/sdk` is the shared machine client for gateways and future products. It currently exposes:
- `feeds()`
- `feed(id)`
- `latest(id)`
- `products(id)`
- `manifest(id)`

### Source-specific surfaces
The API advertises templates for the subdomain strategy discussed for Feedify:

```text
x.feedify.dev   → prompt an X signal feed → Feedify/X bot/x402

git.feedify.dev → prompt a GitHub signal feed → Feedify/X bot/x402/MCP

feedify.dev     → general/corpus/feed creation and social consumption
```

`GET /v1/templates` returns these as machine-readable recipes. `GET /.well-known/feedify.json` advertises the service graph.

## Seed examples

- **Tantrāloka Daily** — corpus-backed distilled insight feed; blog/report-ready
- **Shopify Alpha** — X signal feed with demo X-bot and x402 products
- **Buddha Online** — playful source-grounded synthetic feed
- **New Weird GitHub** — native GitHub discovery source with x402 product

## Local quick start

Prerequisites: Node 22.13+ and npm.

```bash
cp .env.example .env
npm install
npm run seed
npm run dev:api
```

Mobile:

```bash
npm run dev:mobile
```

Feed worker (one pass):

```bash
npm run worker:once
```

Paid x402 gateway:

```bash
npm run dev:x402
```

MCP gateway:

```bash
npm run dev:mcp
```

For a physical phone, set `EXPO_PUBLIC_API_URL` to the API's LAN/deployed URL.

## Public feed formats

For `tantraloka-daily`:

```text
GET /f/tantraloka-daily
GET /f/tantraloka-daily/rss.xml
GET /f/tantraloka-daily/feed.json
GET /f/tantraloka-daily/report.md
GET /f/tantraloka-daily/manifest.json
```

RSS and JSON Feed remain interoperability formats. The app and product gateways use the JSON API directly.

## Worker / automation

`apps/api/src/worker.ts` is the common execution loop:

1. load each Feed
2. fetch normalized source candidates
3. run the FeedProgram once
4. save new immutable items
5. load enabled output channels
6. dispatch the same items to push/product outputs
7. record delivery status

Run once from cron/Cloud Scheduler, or keep it alive with `npm --workspace @feedify/api run worker`.

## Production database

- `supabase/migrations/0001_filterfeed.sql` — original feed/social schema (filename retained to preserve migration history)
- `supabase/migrations/0002_product_chain.sql` — extends `output_channels` and adds auditable output deliveries

The local JSON repository supports old 0.1 data files by backfilling missing `outputs` and `deliveries` arrays when read.

## Security / deployment notes

- Output configs returned publicly are filtered so common secret fields are not exposed.
- Webhooks support an HMAC `x-feedify-signature` using `FEEDIFY_WEBHOOK_SECRET` (or an output-specific env reference).
- OAuth/account tokens stay in environment/secret storage; feed definitions only reference the env name.
- x402 routes remain disabled until a pay-to address is configured.
- X demo outputs remain dry-run by default.
- App Store / Play public UGC still requires production auth, report/block/moderation and legal/privacy work before submission.

## Architecture choices / reuse

We deliberately reuse protocols and upstream infrastructure instead of cloning large projects into this repository:

- Expo SDK 57 for the cross-platform app shell
- Bluesky architecture as a reference for feeds as first-class algorithmic objects
- official x402 Foundation packages for HTTP-native payments
- official MCP TypeScript v2 SDK for agent serving
- JSON Feed 1.1 + RSS 2.0 for portable feed output
- GetXAPI as the cheap X ingestion adapter, isolated behind the source-provider interface
- official X v2 endpoints for account publishing/reposting

No third-party source tree is vendored into Feedify.

## The invariant

> **Feedify is the compiler. A bot, report, blog, agent tool or paid API is just an output node.**

That makes a high-signal feed a reusable media/data asset rather than another timeline configuration.
