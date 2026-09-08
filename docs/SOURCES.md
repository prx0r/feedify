# Source integration notes

These are the verified integration surfaces used by the MVP as of September 8, 2026.

## TrustMRR

Base: `https://trustmrr.com/api/v1`

The `/startups` endpoint supports revenue/MRR/growth/category/team/funding/sale filters and returns verified economics. Standard keys are rate-limited; use derived signals rather than reproducing the database.

Remote MCP: `https://trustmrr.com/api/mcp`
Public discovery MCP: `https://trustmrr.com/api/mcp/discovery`

The MVP auto-selects authenticated MCP when a TrustMRR key exists and otherwise exposes the bounded discovery profile.

## Store Leads

REST base used by MVP: `https://storeleads.app/json/api/v1/all/app`

Remote MCP: `https://storeleads.app/mcp`

The MCP exposes search/get tools across domains, apps, technologies and products. REST is used for deterministic ingestion; MCP is exposed for agent/on-demand exploration.

## Appfigures

Base: `https://api.appfigures.com/v2/`

`/reports/estimates` returns proprietary download/revenue estimates for licensed product IDs. Estimates access depends on plan/license.

## Glama

Directory API: `https://glama.ai/api/mcp/v1/servers`

Glama indexes tens of thousands of MCP servers; Feedify treats new/updated servers as capability primitives and ranks them further using cross-source evidence.

## Apify

Remote MCP: `https://mcp.apify.com`

Use the official Streamable-HTTP MCP to search/fetch/run Actors. With `APIFY_TOKEN`, Feedify auto-registers the authenticated MCP endpoint. Without a token it registers a discovery-only URL limited to Actor/docs search and fetch tools. Production should add explicit tool allowlists and cost budgets before enabling arbitrary Actor execution.

## GitHub

The public Search API is used for recently created repositories with rapid stars. A token raises rate limits. Future GitGoblin integration should supersede this simplistic adapter.

## Hacker News

The public Firebase API is used only as an early-launch source. Feedify filters toward Show HN / API / MCP / agent / marketplace / commerce primitives and gives HN lower evidence weight than proprietary/primary data.
