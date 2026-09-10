# Architecture: Feedify vs Stockify

## The Problem

Right now the stock monitor is tacked onto feedify as extra endpoints. That's wrong. These are two products that share a graph.

## The Architecture

```
FEEDIFY (knowledge graph compiler)          STOCKIFY (portfolio intelligence)
┌─────────────────────────────┐            ┌─────────────────────────────┐
│ X posts → Objects → Edges   │            │ Portfolio → Briefs → Chat   │
│ Convergence detection       │◄──────────▶│ Paper trading (AI vs Human) │
│ Scarcity migration engine   │   GRAPH    │ Daily reports               │
│ AI→Atoms index              │   LAYER    │ Trading theory              │
│ Prediction tracking         │            │ Other traders (X signals)   │
└─────────────────────────────┘            └─────────────────────────────┘
         │                                            │
         ▼                                            ▼
    feedify.egoic.ai                           stockify.egoic.ai
    (public, MCP, research)                    (private, Chris Prior)
```

## Key Insight

**Feedify** = the intelligence layer (what's happening in the world)
**Stockify** = the decision layer (what should I do with my money)

Stockify reads from the feedify graph. It doesn't duplicate the data.

## What Should Happen

1. **Feedify stays as-is** — knowledge graph, X extraction, convergence, scarcity
2. **Stockify becomes its own repo** — portfolio, daily briefs, paper trading, AI chat
3. **Stockify reads from feedify's graph** — shared data, separate products
4. **Chris Prior uses Stockify** — his daily brief, his chat, his paper trades
5. **Feedify stays public** — other users can build their own stockify instances

## The Relationship

```
Feedify: "braaannigan says AI researchers get trapped in local search"
    ↓ (object in graph)
Stockify: "MPAL is up 83% — should I trim?"
    ↓ (references the graph)
Response: "Yes, trim 30%. The bottleneck thesis suggests verification 
          becomes scarce, which benefits MPAL's DSP licences."
```

Feedify provides the intelligence. Stockify provides the decisions.
