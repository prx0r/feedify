# Feedify Vision 2.0 Audit: Current State vs Target Architecture

*Generated: 2026-09-09*

---

## Executive Summary

The current Feedify implementation is a **stateless ranked-reader** that happens to have a `MinimalGraph` and `frontier_schema.py` pointing toward the right architecture. The vision demands a **stateful evolving knowledge graph with delta feeds**. The gap is significant but the existing code has strong bones — adapters, ingestion idempotency, and the feed-as-algorithm concept are all solid foundations.

**Distance rating: 6/10.** The data model is the biggest gap. The pipeline shape is close. The UX model is inverted.

---

## Architecture Comparison

### Data Layer

| Component | Current State | Vision Target | Gap |
|-----------|--------------|---------------|-----|
| **Core tables** | `source_records`, `signals`, `feeds`, `ingestion_runs` | `Artifact`, `Object`, `Edge`, `Feed`, `Interaction`, `Channel` | **MAJOR** — flat signals need to become versioned objects |
| **Graph** | In-memory `MinimalGraph` dataclass (entities + connections) — rebuilt on every API call, never persisted | DB-backed `Object + Edge` with pgvector embeddings | **MAJOR** — graph is ephemeral, needs to be durable |
| **Frontier schema** | `frontier_schema.py` — hardcoded to quantum/AGI labs, Person/Post/Signal/Convergence dataclasses | One generic substrate with `Object.kind` open-ended | **MAJOR** — domain-specific, will explode with Buddhism/commerce/etc. |
| **Event store** | JSONL `EventStore` with no idempotency (10 runs = 1,050 duplicate events) | Single canonical artifact layer in primary DB | **CRITICAL BUG** — duplicates destroy convergence measurement |
| **Insider scoring** | In-memory `SourceReputation`, `SignalMapper` — no persistence | Should become part of object version history | **MODERATE** — good logic, wrong home |
| **Thesis engine** | JSON files in `data/theses/` | Should be versioned objects in graph | **MODERATE** — right idea, wrong storage |
| **Knowledge graph** | `specs/knowledge_graph.json` — static JSON file | Live graph with edges backed by evidence | **MODERATE** — manually curated, needs automation |
| **SQL schema** | SQLite with 4 tables | Postgres + JSONB + pgvector + edges table | **MODERATE** — functional but not production-ready |

### Pipeline Layer

| Component | Current State | Vision Target | Gap |
|-----------|--------------|---------------|-----|
| **Ingestion** | Adapter → `NormalizedItem` → `SourceRecord` → `Signal` — idempotent, 9 adapters | Adapter → `Artifact` → `Object` extraction — same shape, richer output | **MODERATE** — adapter layer is solid, detector output needs to evolve |
| **Detection** | Heuristic detectors (`detect_x`, `detect_sec_edgar`, etc.) producing typed `SignalDraft` | LLM semantic compiler extracting objects + edges from artifacts | **MAJOR** — detectors produce flat signals, not graph updates |
| **Ranking** | Weighted scoring: `novelty*0.27 + actionability*0.28 + ...` + keyword matching | Delta detection: "what changed since user last saw version N?" | **MAJOR** — stateless scoring vs stateful delta |
| **Feed generation** | `get_ranked_feed()` loads all signals, scores, sorts, returns top N | `get_delta_feed()` asks "what object changed since user's last-seen version?" | **MAJOR** — fundamentally different query model |
| **LLM integration** | Optional enrichment hook (not wired into main pipeline), AI chat for insiders | Core semantic compiler that extracts objects/edges from artifacts | **MAJOR** — LLM is peripheral, needs to be central |
| **Brief system** | Jaccard clustering + real-time prices + alpha scoring | Should become cross-source corroboration in graph | **MINOR** — good logic, graph makes it natural |
| **Convergence detector** | Keyword-based topic matching within time window | Graph-based: 2+ independent sources → same object | **MODERATE** — current approach is fragile |

### Output Layer

| Component | Current State | Vision Target | Gap |
|-----------|--------------|---------------|-----|
| **Feed outputs** | JSON, RSS, PWA manifest, MCP tools | JSON, RSS, MCP subscribable resources, x402 | **MINOR** — mostly there |
| **MCP** | Imperative tools (`feedify_signals`, `feedify_graph`) | Subscribable resources with `resources/updated` notifications | **MODERATE** — tools → resources is a protocol change |
| **PWA** | Per-feed manifests + icons for iOS Home Screen | Same + native app eventually | **MINOR** — working well |
| **x402** | Payment middleware implemented but disabled | Payment layer around channels/algorithms | **MINOR** — infrastructure exists |

### Interaction Layer

| Component | Current State | Vision Target | Gap |
|-----------|--------------|---------------|-----|
| **User actions** | None implemented | `DONE`, `SAVE`, `FOLLOW`, `NOISE` at object version level | **MISSING** — no interaction tracking at all |
| **Attention state** | None | `last_seen_version` per user per object | **MISSING** — feed has no memory of what user read |
| **Feed versioning** | Feed has `weights`/`filters` JSON but no version history | Feed programs are versioned, forkable, shareable | **MODERATE** — `FeedProgram` in Filterfeed has version concept |
| **Channel separation** | Feed = both producer and consumer output | Channel (publish) ≠ Feed (consume) | **MISSING** — conflated |

### Filterfeed Integration

| Component | Current State | Vision Target | Gap |
|-----------|--------------|---------------|-----|
| **Shared types** | Filterfeed `@filterfeed/core` has `Feed`, `FeedItem`, `FeedProgram`, `Candidate` | Should share types with Feedify 2 | **MODERATE** — compatible but separate type systems |
| **Feedify provider** | `providers/feedify.ts` fetches from `feedify.egoic.ai/api/signals` | Should consume from Feedify 2's new endpoints | **MINOR** — adapter pattern works |
| **Scoring** | Filterfeed has `scoreCandidate()` with relevance/novelty/quality/actionability | Should share scoring with Feedify 2 | **MINOR** — similar dimensions |
| **Supabase schema** | `profiles`, `feeds`, `feed_versions`, `feed_sources`, `feed_items`, `provenance`, `subscriptions`, `reposts`, `item_feedback`, `output_channels` | Closest to vision target — has versioning, provenance, feedback | **GOOD** — Filterfeed's SQL schema is ahead of Feedify's |

---

## What's Already Close

1. **Adapter architecture** — `NormalizedItem` contract is clean, 9 adapters work, idempotent upsert. This stays.
2. **Feed-as-algorithm concept** — `Feed.prompt` + `Feed.weights` + `Feed.filters` is the seed of `FeedProgram`.
3. **MinimalGraph** — `Entity + Connection` is the right primitive. Just needs to be DB-backed and generic.
4. **Deterministic scoring** — `calculate_base_score()` is good first-pass retrieval. Keep as cheap filter.
5. **Idempotent ingestion** — `source_type + external_id` uniqueness constraint is exactly right for `Artifact`.
6. **Single-service approach** — Deliberately simple. Keep this philosophy.
7. **Product rule** — "feed algorithm is the product object, not the post" is exactly right.
8. **Brief system** — Clustering + cross-source corroboration is graph-native.

## What's Wrong

1. **Signals are flat** — No versioning, no evolution, no "what changed." A signal about LPKF is just another row.
2. **Graph is ephemeral** — `MinimalGraph` is rebuilt from DB on every API call, never stored.
3. **Feed query is stateless** — `get_ranked_feed()` doesn't know what the user has already seen.
4. **Frontier schema is domain-specific** — `Person`, `Post`, `Signal`, `Convergence` are quantum/AGI-only.
5. **LLM is peripheral** — Should be the core semantic compiler, not an optional enrichment hook.
6. **No interaction tracking** — No concept of "user read this" or "user saved this."
7. **Event store has no idempotency** — JSONL `append()` never checks `event_id` existence.
8. **Two parallel graph implementations** — `MinimalGraph` (generic) + `frontier_schema.py` (domain-specific) + `specs/knowledge_graph.json` (static JSON) = confusion.
9. **Feed ≠ Channel** — Currently one object does both jobs.

---

## Recommended Implementation Order (from visionidea2.md)

| # | Task | Current State | Effort | Risk |
|---|------|--------------|--------|------|
| 1 | **Unify data core** — `Artifact` + `Object` + `Edge` tables, delete parallel universes | 4 SQLite tables + JSONL event store + JSON files | HIGH | MEDIUM — must not break live site |
| 2 | **Persist MinimalGraph** — DB-backed `Object + Edge`, generic not domain-specific | In-memory dataclass, rebuilt per request | MEDIUM | LOW — additive |
| 3 | **Evolving objects** — `kind`, `version`, `summary`, `embedding`, `metadata`, `updated_at` | Flat signals with no version | HIGH | MEDIUM — changes core data model |
| 4 | **Add Interaction** — `user_id`, `feed_id`, `object_id`, `object_version`, `action` | Nothing | LOW | LOW — additive |
| 5 | **Delta feeds** — "what important object changed since user last saw version N?" | Stateless `get_ranked_feed()` | HIGH | HIGH — changes feed query model |
| 6 | **Semantic retrieval + LLM reranking** — replace prompt keyword matching | Weighted scoring + keyword matching | MEDIUM | MEDIUM — keep deterministic as fallback |
| 7 | **ChatGPT importer** — extract ideas/theories/problems from conversations | Nothing | MEDIUM | LOW — new feature |
| 8 | **Separate Channel from Feed** | Conflated in `Feed` model | MEDIUM | MEDIUM — API changes |
| 9 | **Versioned/shareable feed algorithms** | `Feed.weights`/`Feed.filters` JSON | LOW | LOW — extends existing model |
| 10 | **MCP subscribable resources** | Imperative MCP tools | MEDIUM | LOW — additive endpoint |

---

## Key Insight

The Filterfeed Supabase schema (`0001_filterfeed.sql`) is actually **closer to the vision** than Feedify's current schema. It already has:
- `feed_versions` (versioned programs)
- `feed_sources` (per-version source config)
- `provenance` (source attribution per item)
- `item_feedback` (user actions)
- `output_channels` (publisher separation)

Feedify 2 should adopt this schema shape and extend it with `objects`, `edges`, `artifacts`, and `interactions` tables.

---

## Risk Assessment

**Breaking the live site:** The current `feedify.egoic.ai` runs from `/root/feedify`. As long as we develop in `/root/feedify2` and deploy to `v2.feedify.egoic.ai`, the live site is untouched.

**Data migration:** The biggest risk is migrating existing signals into the new Object model. Recommendation: start with a clean DB for v2, re-ingest from adapters. The adapters are idempotent so re-ingestion is safe.

**LLM costs:** The semantic compiler will call LLM for object extraction. Budget: ~$0.01 per artifact for DeepSeek V3, ~$0.10 for GPT-5-mini. At 100 artifacts/day, that's $1-10/day.

**Complexity:** The vision is ambitious. Mitigation: ship incrementally. Phase 1 = data model + graph persistence. Phase 2 = delta feeds. Phase 3 = channels + MCP resources.
