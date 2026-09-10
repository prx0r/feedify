# Feedify Recipes — Common Tasks and Patterns

## The loop every recipe lives in

```
INGEST posts ──► CLASSIFY objects ──► BUILD edges ──► DETECT convergence
       ▲                                              │
       │                                              ▼
       └──────── FEED watches graph ◄── PREDICTIONS tracked
```

Feedify sees: artifacts, objects, edges, convergences. It never stops watching.

---

## Recipe 1: Extract a new account

```python
from feedify.adapters.x import XAdapter
from feedify.services.ingestion import upsert_artifact
from feedify.services.detector import classify_and_extract

async with XAdapter() as adapter:
    tweets = await adapter.fetch(limit=50)
    for tweet in tweets:
        artifact, created = upsert_artifact(session, tweet)
        if created:
            classify_and_extract(session, artifact, tweet)
```

**Key**: Always paginate with cursor and use date filters:
```python
params = {"q": f"from:{handle} since:2026-08-01 until:2026-08-31", "count": 20, "cursor": cursor}
```

---

## Recipe 2: Detect convergence

```python
from feedify.services.convergence import detect_convergence

convergences = detect_convergence(
    session,
    days=7,           # look back 7 days
    min_authors=2,    # at least 2 different authors
    min_experimenters=1,  # at least 1 with source_distance=0
)
```

Returns convergences where multiple source_distance=0 accounts discuss the same topic on the same day.

---

## Recipe 3: Track a prediction

```python
from feedify.models import Object, Edge

# Create prediction
prediction = Object(
    object_key="prediction:ai_bottleneck",
    kind="prediction",
    title="AI will make verification the next bottleneck",
    summary="...",
    confidence=0.7,
    domain="bottleneck",
)
session.add(prediction)

# When evidence appears, connect it
evidence = Object(...)  # the supporting observation
edge = Edge(
    source_id=evidence.id,
    target_id=prediction.id,
    relation="supports",
    weight=0.8,
)
session.add(edge)
```

---

## Recipe 4: Build scarcity chain

```python
from feedify.models import Object, Edge

# Create scarcity nodes
verification = Object(object_key="bottleneck:verification", kind="theory", ...)
instruments = Object(object_key="bottleneck:instruments", kind="theory", ...)

# Connect: verification → instruments
edge = Edge(
    source_id=verification.id,
    target_id=instruments.id,
    relation="leads_to",
    weight=0.7,
    metadata_json={"mechanism": "bottleneck_migration"},
)
```

---

## Recipe 5: World-State Consistency Check

```python
from feedify.models import Object, Edge

# Find stocks with contradictory implied worlds
contradictions = session.scalars(
    select(Edge).where(Edge.relation == "contradicts_world")
).all()

for c in contradictions:
    stock_a = session.get(Object, c.source_id)
    stock_b = session.get(Object, c.target_id)
    print(f"{stock_a.title} ↔ {stock_b.title}")
    print(f"  Contradiction: {c.metadata_json.get('contradiction')}")
```

---

## Recipe 6: Technical half-life screening

```python
from feedify.models import Object

# Find short candidates (mismatch >= 5 years)
half_life_objects = session.scalars(
    select(Object).where(
        Object.metadata_json["sector"].as_string() == "technical_half_life"
    )
).all()

for obj in half_life_objects:
    data = obj.metadata_json
    if data.get("mismatch", 0) >= 5:
        print(f"SHORT: {data['asset']} — H_tech={data['h_tech']}yr, H_val={data['h_val']}yr")
```

---

## Recipe 7: Delta feed (what changed)

```python
from feedify.services.feeds import get_delta_feed

# Get what changed since user last saw each object
items = get_delta_feed(
    session,
    feed=feed,
    user_id="user123",
    limit=50,
)

for item in items:
    if "delta" in item:
        print(f"UPDATED: {item['title']}")
    else:
        print(f"NEW: {item['title']}")
```

---

## Recipe 8: Import a ChatGPT conversation

```python
from feedify.services.chatgpt_importer import import_conversation

objects, edges = await import_conversation(
    session,
    text="full conversation text...",
    title="My ChatGPT conversation",
)
# Extracts: ideas, theories, problems, decisions, predictions, picks
```

---

## Recipe 9: Score an account

```python
from feedify.services.detector import get_source_proximity, compute_expected_alpha

# Get source proximity (0=experimenter, 5=influencer)
proximity = get_source_proximity("braaannigan")  # 0.95

# Compute expected alpha for a post
alpha = compute_expected_alpha(
    source_proximity=0.95,
    novelty=0.7,
    bottleneck_relevance=0.8,
    specificity=0.6,
    surprise=0.6,
)
```

---

## Recipe 10: Build AI→Atoms index

```python
from feedify.models import Object, Edge

companies = [
    {"ticker": "KEYS", "name": "Keysight", "cross_world": 0.9},
    {"ticker": "KLAC", "name": "KLA", "cross_world": 0.85},
]

for c in companies:
    obj = Object(
        object_key=f"company:{c['ticker']}",
        kind="company",
        title=f"{c['ticker']} — {c['name']}",
        confidence=c["cross_world"],
        domain="materials",
    )
    session.add(obj)
```
