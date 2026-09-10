# Extraction Process Review — How to Avoid Slop

**Date**: 2026-09-10
**Context**: After ingesting @DeepDishEnjoyer's 23 August tweets — all became generic `claim` objects with no intellectual content extracted.

## What Went Wrong

### 1. Heuristic detector treats all X replies as generic claims

The `compile_x` function in `detector.py` does this:

```python
# If no scarcity keywords match:
objects.append(ObjectDraft(
    object_key=f"idea:observation:{item.title.lower().replace(' ', '_')[:48]}",
    kind="claim",
    title=item.title,           # Raw tweet text truncated to 160 chars
    summary=(item.body or "")[:700],  # Raw tweet body
    confidence=0.55,
    domain=infer_domain(item),
    tags=["x"],
))
```

Result: "cybersecurity isn't scary. bio is" becomes a `claim` object with that exact text as the summary. No extraction of *what the person actually means*, *what domain it applies to*, *what it contradicts or supports*.

### 2. No source_distance modeling

The system creates a `person` entity with:
```python
summary=f"X user with {followers:,} followers."
```

This is useless. The Feedify thesis says the key property is `source_distance` (0 = running experiments, 5 = influencer). The current system doesn't model this at all.

### 3. No claim classification

Every X post becomes kind=`claim`. But the aithesis people document shows these are actually:
- `theory` — "the bottleneck moved somewhere else a long time ago" (Chayenne Zhao)
- `observation` — "my autonomous researcher keeps getting trapped in local search" (Liam Brannigan)
- `evidence_for` — "AnchorDream produced consistent improvements across 3 tasks" (Junjie Ye)
- `problem` — "models jump to hyperparameter optimization too early" (Liam Brannigan)
- `decision` — "human data scales better than robot-specific collection" (Edward Miller)

### 4. No relationship extraction

The system doesn't connect posts to each other. When Chayenne Zhao says "the bottleneck moved" and Liam Brannigan says "my researcher gets trapped in local search", these are *the same insight from different angles*. The system should create an edge between them.

### 5. No claim_lead_time tracking

The aithesis document describes the killer metric: researcher says X at t₀ → evidence appears at t₁ → corporate acknowledgement at t₂ → market consensus at t₃. The current system has no mechanism for this.

### 6. The watchlist approach is too blunt

Adding 100 accounts to a JSON file and fetching their recent N posts is inefficient because:
- It fetches the same accounts every time
- It doesn't prioritize high-information posts
- It doesn't recursively expand from interesting posts
- It doesn't use the scoring formula from the aithesis document

### 7. The LLM compiler is the real solution — but it's optional

The `llm_compiler.py` I created would actually extract typed objects and edges. But:
- It's only called for `x`, `sec_edgar`, `openinsider` sources
- It falls back to heuristic when `llm_api_key` is empty
- Even when called, it sees raw tweet text, not the context of who posted it

## How to Fix It

### Fix 1: Make the LLM compiler the primary path for X posts

The heuristic detector should be a *fallback only*. For X posts from the watchlist, always use the LLM compiler because:
- It can classify the claim type (theory/observation/problem/decision/evidence_for)
- It can extract the actual intellectual content
- It can create edges between related posts

### Fix 2: Add source_distance to the watchlist

The watchlist entries should include:
```json
{
  "handle": "braaannigan",
  "source_distance": 0,
  "domain": "ai-research",
  "lab": "",
  "role": "hands-on AI researcher"
}
```

And the detector should use this to set `source_proximity` on objects:
- source_distance=0 → source_proximity=0.95
- source_distance=1 → source_proximity=0.85
- source_distance=2 → source_proximity=0.7
- source_distance=3 → source_proximity=0.5
- source_distance=4 → source_proximity=0.3
- source_distance=5 → source_proximity=0.1

### Fix 3: Add claim classification to the LLM compiler prompt

The LLM compiler should be told:
```
Classify each claim as one of:
- theory: causal claim about how something works
- observation: empirical report of what was seen
- problem: something that's broken or suboptimal
- decision: a choice that was made
- prediction: claim about what will happen
- evidence_for: data supporting an existing theory
- evidence_against: data contradicting an existing theory
- question: open question worth tracking
- pick: specific company/tool/person recommended

Use "theory" for bottleneck claims, "observation" for experimental results,
"problem" for failure modes, "evidence_for" for supporting data.
```

### Fix 4: Add relationship extraction to the LLM compiler

The compiler should also extract edges:
```
For each object, check if it relates to any previously extracted object:
- supports: agrees with or reinforces
- contradicts: disagrees with or challenges
- supersedes: replaces or updates
- causes: one thing leads to another
- related_to: general connection

If the post mentions a specific person, company, or concept that already exists
as an object, create a "mentions" edge.
```

### Fix 5: Add claim_lead_time tracking

When a `theory` object is created, store:
```json
{
  "claimed_at": "2026-03-15",
  "claimed_by": "GenAI_is_real",
  "claim_text": "the bottleneck moved somewhere else a long time ago",
  "evidence_at": null,
  "corporate_ack_at": null,
  "market_consensus_at": null,
  "lead_time_days": null
}
```

When evidence appears later (e.g., an NVIDIA earnings call mentions the same bottleneck), update the object:
```json
{
  "evidence_at": "2026-09-01",
  "lead_time_days": 169
}
```

This is the "learned information-propagation graph" the aithesis document describes.

### Fix 6: Add recursive expansion

Instead of just fetching the last N posts from each watchlist account:
1. Fetch recent posts
2. For each high-scoring post, fetch who they replied to
3. For each reply, check if the replier is already in the graph
4. If not, fetch their recent posts
5. Repeat recursively (with depth limit)

This is how you discover the 43-follower accounts that the aithesis document describes.

### Fix 7: Add the scoring formula to the detector

The detector should score each post using:
```
Expected Alpha/Post = (source_proximity × novelty × bottleneck_relevance × specificity × surprise) / (promotion + repetition + consensus_saturation + performative_posting)
```

Where:
- `source_proximity` comes from `source_distance` (0=experimenter, 5=influencer)
- `novelty` = 1 - max_jaccard_similarity against recent posts
- `bottleneck_relevance` = keyword matching against bottleneck ontology
- `specificity` = presence of specific numbers, mechanisms, names
- `surprise` = inverse of how common the claim is
- `promotion` = presence of self-promotion signals
- `repetition` = how many times this claim has been made before
- `consensus_saturation` = how widely accepted this claim is
- `performative_posting` = engagement-bait signals

Posts scoring below a threshold should be skipped entirely.

## Priority Order

1. **Make LLM compiler primary for X posts** — this alone would fix 80% of the slop
2. **Add source_distance to watchlist** — enables proper source_proximity scoring
3. **Add claim classification** — theory vs observation vs problem vs evidence
4. **Add the scoring formula** — filter out low-alpha posts before ingestion
5. **Add recursive expansion** — discover unknown high-signal accounts
6. **Add claim_lead_time tracking** — the information-propagation graph
7. **Add relationship extraction** — connect posts to each other

## The Core Insight

The current system is a **Twitter RSS reader** — it ingests everything and creates generic objects.

The target system is an **information-propagation graph** — it scores posts before ingestion, extracts typed knowledge, tracks when claims become consensus, and recursively discovers new high-signal sources.

The gap is not data access. The gap is intelligence about what to extract and what to skip.
