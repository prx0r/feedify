# Architecture

## Pipeline

```text
UPSTREAM SOURCES
  REST APIs | RSS | GitHub | remote MCP | marketplace data | X provider
       |
       v
NormalizedItem
       |
       v
SourceRecord (raw evidence + normalized metrics)
       |
       v
Signal detector
       |
       +--> typed Signal
       |      novelty/actionability/source-proximity/evidence/confidence
       |
       v
Feed algorithm
  prompt + deterministic weights + filters + freshness
       |
       v
Ranked items
       |
       +--> web
       +--> iOS PWA launcher
       +--> RSS
       +--> JSON
       +--> MCP
       +--> x402 paid JSON
```

## Why not a generic vector search feed?

Vector similarity answers "is this text semantically related?" It does not answer whether a source is primary, economically validated, newly enabled, replicable, or redundant. Feedify models those attributes explicitly.

## Why source adapters and detectors are separate

A Store Leads row and TrustMRR row look unrelated upstream, but both can express a comparable economic signal after normalization. This is what allows feed algorithms to work across sources.

## Why a feed is versionable code

The long-term object is effectively:

```json
{
  "prompt": "...",
  "weights": {"novelty": 1.4, "actionability": 1.5},
  "filters": {"domains": ["commerce", "agents"], "min_score": 0.75}
}
```

That object can be forked, backtested, sold and exposed as an endpoint. The UI is just one renderer.
