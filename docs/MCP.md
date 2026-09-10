# Feedify MCP Server — Future Design

## Current MCP Tools (11)

| Tool | Description |
|------|-------------|
| `feedify_health` | System health |
| `feedify_objects` | List objects (domain, kind filters) |
| `feedify_insiders` | Insider decisions and claims |
| `feedify_frontier` | Frontier objects |
| `feedify_graph` | Knowledge graph context |
| `feedify_chat` | Chat with Feedify AI |
| `feedify_feeds` | List feed algorithms |
| `feedify_sources` | List data sources |
| `feedify_compiled_feed` | Run compiled feed pipeline |
| `feedify_delta` | Get delta feed |
| `feedify_import_chatgpt` | Import conversations |

## Future: Subscribable Resources

The MCP spec supports resource subscriptions with `resources/updated` notifications. This is the natural delivery interface for Feedify.

### Resource URIs

```
feedify://graph                    # Full knowledge graph
feedify://convergence               # Active convergences
feedify://predictions               # Predictions with evidence
feedify://scarcity                  # Scarcity migration chains
feedify://companies                 # AI→Atoms index
feedify://half-life                  # Technical half-life data
feedify://feeds/{slug}               # Specific feed
feedify://feeds/{slug}/delta         # Delta for specific feed
```

### Subscription Flow

```
Agent subscribes to feedify://convergence
        │
        ▼
Feedify watches graph for new convergences
        │
        ▼
When convergence detected:
  Feedify emits resources/updated notification
        │
        ▼
Agent reads updated resource
```

### Implementation Plan

1. Add resource endpoints to Feedify API
2. Add WebSocket support for real-time updates
3. Implement MCP resource subscription protocol
4. Wire convergence detection to resource notifications

## Future: Paid Feeds via x402

Feedify already has x402 integration (`feedify/x402.py`). Future:

```
GET /api/paid/feeds/{slug}.json
  → 402 Payment Required
  → Client pays via Algorand/EVM
  → Feed delivered
```

See `integrations/feedify/X402.md` for deployment guide.
