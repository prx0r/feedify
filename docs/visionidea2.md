# Feedify Vision 2.0

Yes. The graph direction is right, but I would change what the graph **means**.

Feedify should not fundamentally be:

> sources → posts → scores → ranked feed

It should become:

> **world/personal events → evolving knowledge → programmable attention**

That distinction fixes almost everything you are describing.

Your current README already points in the right direction by making the **feed algorithm**, rather than the post, the product object.  But the implementation beneath it is still mostly a stateless ranked-reader architecture.

## The architecture I would converge on

```text
                         ┌─────────────────────────┐
                         │ X / SEC / GitHub / web  │
                         │ ChatGPT / notes / blogs │
                         │ papers / RSS / users    │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         IMMUTABLE ARTIFACTS/EVENTS
                         exact original + provenance
                                      │
                                      ▼
                          LLM SEMANTIC COMPILER
                 extract / merge / resolve / update
                                      │
                 ┌────────────────────┼─────────────────────┐
                 ▼                    ▼                     ▼
              ENTITIES             OBJECTS                EDGES
          LPKF, Nvidia, Tom     idea / theory /       supports
          person, concept      problem / pick /       contradicts
          technology           claim / question       causes
                               prediction / thread    supersedes
                 └────────────────────┬─────────────────────┘
                                      │
                              LIVE KNOWLEDGE GRAPH
                                      │
                                      ▼
                              FEED PROGRAMS
                   "AI acceleration → overlooked stocks"
                   "my recurring founder problems"
                   "best Buddhist ideas"
                   "new theories"
                   "portfolio counter-evidence"
                                      │
                                      ▼
                         USER/AGENT ATTENTION STATE
                     seen / save / dismiss / follow
                       last-seen object version
                                      │
                                      ▼
                              DELTA FEED
                       only what matters NOW
```

The most important word there is **delta**.

### Right now Feedify ranks things. It needs to understand what changed.

The existing `get_ranked_feed()` takes the latest 1,000 `Signal`s, calculates a score, sorts them, and returns the top N.  And `score_signal()` is basically weighted static attributes + freshness + literal prompt keyword matches.

That's a good bootstrap. It is not the eventual Feedify.

Imagine your `AI acceleration` feed.

Today:

```text
LPKF thesis       0.91
SUSS backlog      0.88
LEU contract      0.86
LPKF article      0.84
old SUSS post     0.82
...
```

You read them.

Tomorrow you don't want another rearrangement of those exact ideas.

You want:

```text
↑ LPKF / glass packaging
NEW: independent TSMC evidence supports the bottleneck thesis.
3 new pieces of evidence since you last saw this.
Confidence 71% → 78%.

⚠ SUSS
NEW COUNTER-EVIDENCE: order timing slipped.
This weakens your "2027 revenue inflection" claim.

NEW THEORY
Three independent sources now imply optical inspection
may become the NEXT bottleneck after packaging.

NEW COMPANY
Nynomic connected to 4 entities already in your bottleneck graph.
Previously absent from your portfolio universe.
```

That is radically more valuable than a better Twitter ranking algorithm.

---

## Your graph instinct is correct — but don't build a giant ontology

There are currently several competing architectures in the repo.

| Current component                         | Assessment                                                                       |
| ----------------------------------------- | -------------------------------------------------------------------------------- |
| `SourceRecord → Signal → Feed` SQL models | Good ingestion MVP, too flat                                                    |
| `MinimalGraph`                            | **Best architectural direction**                                                 |
| `frontier_schema.py`                      | Too domain-specific                                                              |
| `RealityEvent / GenericEvent`             | Right event-sourcing idea, separate implementation is a problem                  |
| L0-L4 Reality hierarchy                   | Excellent as a feed-specific inference strategy, not as your global schema       |
| hardcoded feed ranking                    | Good bootstrap, should become candidate retrieval rather than final intelligence |

Your `MinimalGraph` says almost exactly what I would preserve: entities + connections, with the LLM supplying semantic intelligence and the graph supplying memory, provenance and cheap structure.

By contrast, `frontier_schema.py` already has special `IONQ`, `INFLEQTION`, `IQM`, `QUANTUM_LEAD`, `AGI_LEAD`, etc.  That will explode as soon as you add Buddhism, jokes, commerce, personal ChatGPT conversations and ten thousand arbitrary user feeds.

Don't make:

```text
QuantumGraph
StockGraph
BuddhistGraph
ChatGPTGraph
JokeGraph
CommerceGraph
```

Make one almost stupidly generic substrate.

## The minimal durable model

I'd reduce the semantic core to approximately this:

| Object        | Purpose                                                         |
| ------------- | --------------------------------------------------------------- |
| `Artifact`    | Immutable input: tweet, filing, message, paper, note, blog post |
| `Object`      | Something meaningful discovered from artifacts                  |
| `Edge`        | Relationship between objects, backed by evidence                |
| `Feed`        | A versioned attention program                                   |
| `Interaction` | What a user/agent did with an object                            |
| `Channel`     | Something a creator publishes/subscribers follow                |

And `Object.kind` is deliberately open:

```text
entity
person
company
technology
idea
claim
theory
problem
question
decision
prediction
pick
joke
concept
thread
...
```

No migration is required when someone invents:

> "Show me unresolved philosophical contradictions I've repeatedly encountered while studying Abhinavagupta."

The LLM figures out the semantics.

Edges can stay similarly tiny:

```text
mentions
related_to
supports
contradicts
supersedes
causes
depends_on
evidence_for
authored_by
about
```

The graph doesn't have to understand philosophy.

The model does.

### And I would not introduce Neo4j.

Postgres + JSONB + pgvector + a straightforward `edges` table is enough for a very long time.

Your existing single-service approach is sensible. The README explicitly keeps Feedify as one Python service until usage forces decomposition.  Keep that philosophy.

No Kafka. No microservice zoo. No enormous knowledge-graph framework.

---

## The thing I think you're reaching for: evolving objects

This is the missing primitive.

Instead of every insight being another post, something like:

```text
object_id: theory:ai-physical-bottleneck
kind: theory
version: 17

current_state:
  "As AI makes generation increasingly cheap,
   physical validation, packaging and energy become
   progressively more important constraints."

confidence: 0.82

evidence:
  → SUSS orders
  → LPKF qualification
  → TSMC remarks
  → arXiv autonomous design work
  → grid interconnection data

contradictions:
  → packaging capacity ramp faster than predicted

related:
  → LPKF
  → SUSS
  → LEU
  → Nynomic
```

Every time relevant information arrives, Feedify asks:

> **Does this change an existing object or create a genuinely new object?**

If it changes one:

```text
version 17 → 18
```

Now your interaction can simply contain:

```text
user last saw version = 17
```

Version 17 disappears.

Version 18 resurfaces.

This solves your "tap when I've seen it" problem beautifully.

You don't actually want:

> hide tweet 847294 forever.

You want:

> **don't bother me about this knowledge state again until something materially changes.**

That's the Feedify UX.

---

## ChatGPT history could be an absurdly good Feedify source

An uploaded conversation shouldn't become 50,000 chat messages in a searchable database.

It should compile into your personal graph.

For example, hundreds of conversations might generate:

```text
IDEA
Feedify: user-programmable information algorithms

IDEA
Feedify: x402 machine-consumable intelligence

THEORY
Physical bottleneck migration under AI acceleration

RECURRING PROBLEM
Too many simultaneous startup projects

RECURRING PROBLEM
Account/business setup operations are difficult to automate

DECISION
Feedify website before native app

DECISION
GitGoblin remains private technical-alpha source

OPEN QUESTION
How to measure source signal before price discovery?

PICK
LPKF

PICK
LEU

PROJECT
Feedify

PROJECT
GeoDrop
```

And then edges:

```text
GitGoblin
   └─ supplies_signal_to → Feedify

AI acceleration thesis
   ├─ supports → LPKF thesis
   ├─ supports → SUSS thesis
   └─ motivates → Reality Feed

Feedify
   ├─ solves → information overload
   └─ related_to → custom algorithms

Project overload
   ├─ recurring_problem_for → user
   └─ motivates → studio orchestration
```

Then you could literally create:

> **"My best unrealised ideas"**

or

> **"Problems I've complained about at least five times but still haven't solved"**

or

> **"Ideas I repeatedly return to after abandoning them"**

or

> **"What changed in my worldview this month?"**

Those are feeds.

That is much more interesting than "import ChatGPT and search it."

---

## And this also gives you your Substack-for-agents concept

I think you need to distinguish **Channel** from **Feed**.

A **Channel** is something someone publishes.

A **Feed** is an algorithm someone uses to consume information.

Tom might publish:

```text
@tom/ai-acceleration
@tom/frontier-companies
@tom/founder-experiments
```

But I could consume:

```text
"My semiconductor feed"

INPUTS:
  @tom/ai-acceleration
  SemiAnalysis
  SEC
  TSMC filings
  arXiv
  GitHub

INSTRUCTIONS:
  Find bottlenecks that are becoming economically binding.
  Prefer evidence nobody else in my graph has connected.
  Strongly prioritize investable companies < $5B.
  Suppress things I've already internalized.
```

That separation is essential.

It also makes Feedify simultaneously:

**Substack** — publish intelligence channels.

**Bluesky custom feeds** — algorithms themselves become shareable products. Bluesky's official API actually exposes feed-generator primitives and custom-feed algorithms, validating that algorithms can be first-class social objects. ([Bluesky][1])

**Readwise-like personal knowledge ingestion** — private sources become inputs.

**MCP for intelligence** — agents consume the same feeds.

**x402** — some channels/algorithms can be paid.

That is a coherent product rather than five different features.

---

## Agents should get streams, not repeatedly call `get_feed`

Your current MCP implementation exposes imperative tools such as `feedify_signals`, `feedify_graph` and `feedify_feeds`.

For what you're building, a Feedify feed is naturally an **MCP Resource**.

Current MCP explicitly supports resource subscriptions and `resources/updated` notifications. ([Model Context Protocol][2])

So eventually:

```text
feedify://tom/ai-acceleration
feedify://me/stock-alpha
feedify://me/open-problems
```

Agent subscribes.

Something materially changes.

Feedify emits update.

Agent reads delta.

This is extremely aligned with the product.

---

## Feed algorithms should become stateful programs

I would stop thinking of:

```python
weights = {
    "novelty": 1.35,
    "actionability": 1.45
}
```

as the algorithm.

That's merely stage-one candidate retrieval.

The actual feed definition can remain natural language:

```text
Find genuinely new evidence concerning the AI acceleration thesis.

Prioritize:
- new physical bottlenecks
- hidden public companies
- first-principles experts
- primary evidence

Prefer contradictions to repetition.

Never show me an idea I've already seen unless its evidence,
confidence or implications changed materially.
```

Feedify compiles that into approximately:

```text
candidate retrieval
    ↓
semantic similarity
    ↓
graph expansion
    ↓
new-information/delta detection
    ↓
source reputation
    ↓
LLM relevance judgement
    ↓
diversity / repetition policy
    ↓
user-state suppression
```

Use cheap deterministic/vector retrieval to reduce thousands of objects to perhaps tens of candidates, then let the LLM do the sophisticated judgement.

That's the 80/20 solution.

Don't try to encode "what constitutes a genuinely novel scientific insight" in fifty SQL columns.

---

## I'd make the ranking objective **information gain**, not engagement

For Feedify, "like" is almost the wrong primitive.

The key user actions are closer to:

```text
DONE       I've absorbed this.
SAVE       This matters; retain prominently.
FOLLOW     Alert me when this thread changes.
NOISE      This was not useful.
```

Internally you can still model arbitrary reactions.

But `DONE` is especially important.

And because feeds are based on evolving objects:

```text
DONE theory:v17
```

doesn't prevent:

```text
theory:v18
```

from appearing.

That's the missing feedback loop you were describing.

---

## There is also a serious current ingestion problem to fix first

Your Reality architecture concept is strong: raw world → immutable events → state transitions → causal graph. But the implementation now has a separate JSONL event store whose `append()` never checks whether an `event_id` already exists.

And your latest 10-run test demonstrates the consequence: each run finds 105 events and the total climbs all the way to 1,050.

So right now:

```text
same SEC fact
same SEC fact
same SEC fact
same SEC fact
...
```

can masquerade as ten observations.

That is catastrophic once you start measuring convergence.

Your existing SQL `SourceRecord` model already has a uniqueness constraint on `(source_type, external_id)`.

There should be **one canonical provenance/event layer**, not SQL ingestion plus another Reality JSONL universe.

---

## What I would implement now

In this exact order:

1. **Unify the data core.** Keep immutable artifacts/events in the primary DB. Delete the parallel semantic universes. Preserve raw provenance forever.

2. **Persist the MinimalGraph.** Convert its generic `Entity + Connection` philosophy into DB-backed `Object + Edge`. Make it source-agnostic rather than X-specific; the present frontier graph is explicitly built around X signals and a watchlist.

3. **Introduce evolving objects.** Add `kind`, `version`, `summary`, `embedding`, `metadata`, `updated_at`. Claims/theories/problems/picks become stable objects that change version when knowledge changes.

4. **Add `Interaction`.** `user_id`, `feed_id`, `object_id`, `object_version`, `action`, `created_at`. Immediately implement `DONE`, `SAVE`, `FOLLOW`, `NOISE`.

5. **Change feed generation from signals → object deltas.** A feed should ask: "what important object has changed since this user last saw its version?"

6. **Replace literal prompt matching with semantic candidate retrieval + LLM reranking.** Keep the current deterministic score as cheap first-pass filtering and explanations, not final judgement.

7. **Build the ChatGPT/conversation importer as the proving ground.** Extract ideas, theories, recurring problems, decisions, predictions and unresolved questions. If the generic architecture handles this *and* SEC filings *and* jokes without schema changes, you've found the right abstraction.

8. **Separate Channel from Feed.** Channel = producer output. Feed = consumer algorithm. This unlocks the Substack/social layer without corrupting the intelligence architecture.

9. **Make feed algorithms versioned/shareable/forkable.** The algorithm itself can have an author, history, subscribers and eventually reputation/performance.

10. **Upgrade MCP feeds to subscribable resources.** JSON/RSS remain compatibility outputs; MCP becomes the native agent delivery interface and x402 becomes the payment layer around the same underlying stream. MCP already has the exact subscription semantics required. ([Model Context Protocol][2])

The conceptual compression is:

> **Feedify is not an AI RSS reader.**
>
> **Feedify is a compiler that turns arbitrary information into a continuously maintained personal/world model, and turns natural-language attention policies into live views over changes in that model.**

That architecture accommodates your stock-alpha use case, AI-acceleration theories, uploaded ChatGPT history, recurring problems, Buddhist ideas, jokes, blogs, paid intelligence channels and autonomous agents **without needing a separate product architecture for any of them**.

And the strongest insight in the repo is already pointing there: immutable evidence underneath, minimal graph in the middle, LLM intelligence above it, and user-defined feeds as the output. The main job now is to collapse the duplicate schemas and make the feed **stateful over evolving knowledge rather than stateless over posts**.

[1]: https://docs.bsky.app/docs/starter-templates/bots?utm_source=chatgpt.com "Tutorials - AT Protocol"
[2]: https://modelcontextprotocol.io/specification/draft/server/resources?utm_source=chatgpt.com "Resources - Model Context Protocol"
