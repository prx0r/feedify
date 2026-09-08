# Feed → Product Chain

Feedify 0.2 introduces a single `OutputChannel` registry. This is intentionally not a separate bot/report/payments subsystem per use case.

## Chain graph

`GET /v1/feeds/:id/chain` returns nodes and edges so UI or agents can render:

```text
source:x-search ─┐
source:rss ──────┼─> feed:shopify-alpha ─┬─> output:feedify
source:github ───┘                       ├─> output:x-bot
                                         ├─> output:x402
                                         └─> output:report
```

## Delivery semantics

Pull outputs (`public_web`, `rss`, `json_feed`, `mcp`, `x402`) do not duplicate items and require no delivery record for each read.

Push/materialized outputs (`x_bot`, `webhook`, later email/Telegram) create `OutputDelivery` rows. Blog/report outputs currently return deterministic dry-run materialization records until a storage/CMS adapter is attached.

## Why immutable FeedItems matter

A repost, X bot publication, paid API response and report can all point back to the same item id and provenance. Editing ranking logic creates a new feed version; it does not mutate historical items.
