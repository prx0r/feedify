# Next Steps — Feedify 2.0

**Created**: 2026-09-10
**Status**: Core infrastructure complete. Ready for intelligence layer.

---

## What's Done

| Component | Status |
|-----------|--------|
| Data model (7 tables) | ✅ |
| 102 X accounts extracted | ✅ |
| 3,357 tweets ingested | ✅ |
| 7,046 objects classified | ✅ |
| 5,207 edges built | ✅ |
| 145 convergences detected | ✅ |
| 343 predictions tracked | ✅ |
| 109 predictions with evidence | ✅ |
| API endpoints working | ✅ |
| 41 tests passing | ✅ |
| Deployed at v2.feedify.egoic.ai | ✅ |

---

## What's Next (Priority Order)

### 1. Build the Scarcity Migration Engine
**What**: For every capability shock, trace: what becomes abundant → what complement receives induced demand → can supply respond → what's the next constraint.

**How**:
- Take the 388 theories in the graph
- For each, ask: "What does this make scarce?"
- Create `Edge(relation="makes_scarce")` to the bottleneck
- Build a chain: abundance → scarcity → investment → relief → next scarcity

**Files to modify**: `feedify/services/ingestion.py` (add scarcity extraction)

### 2. Build the AI→Atoms Index
**What**: Universe of companies in the "interface layer" — test, measurement, characterization, automation, control, verification, certification.

**How**:
- Search for public companies in: Keysight, Oxford Instruments, FormFactor, KLA, Tecan, Bruker, UL Solutions, etc.
- Score each for cross-world necessity (how many different futures need them?)
- Build `Object(kind="company")` for each
- Connect to theories via `Edge(relation="serves_bottleneck")`

**Files to create**: `feedify/services/ai_atoms_index.py`

### 3. Build World-State Consistency Arbitrage
**What**: Reverse-DCF thousands of companies. Find pairs whose valuations require contradictory futures.

**How**:
- For each major stock, infer what world its price requires
- Find pairs where `P(W_A AND W_B) << market_implied`
- Create `Object(kind="theory")` for each inconsistent world-state
- Track which stocks contradict each other

**Files to create**: `feedify/services/consistency_arbitrage.py`

### 4. Build the Real Usage → Economic Destruction Graph
**What**: Map actual AI task consumption to affected labor → affected companies → induced complement demand.

**How**:
- Use OpenRouter token data (when available)
- Map task types to affected occupations
- Map occupations to affected companies
- Create `Edge(relation="substitutes")` from AI task to human labor
- Create `Edge(relation="induces_demand")` from AI task to complement

**Files to create**: `feedify/services/usage_graph.py`

### 5. Build Technical Half-Life / Obsolescence Short Engine
**What**: Estimate survival of business models vs valuation duration.

**How**:
- For each company, estimate `H_tech` (technological half-life)
- Compare with `H_valuation` (how much duration is priced in)
- Large positive mismatch = short candidate
- Create `Object(kind="prediction")` for each mismatch

**Files to create**: `feedify/services/half_life_engine.py`

---

## What NOT to Do

1. **Don't add more X accounts** until the 102 we have are fully analyzed
2. **Don't build a native app** until the intelligence layer is working
3. **Don't add more source adapters** until the graph is useful
4. **Don't optimize the UI** until the data model is final
5. **Don't deploy to production** until the intelligence layer is proven

---

## The One Sentence

> Feedify is not an AI RSS reader. It's the sensory nervous system for a moving scarcity surface — tracking what becomes abundant, what that makes scarce, who owns the scarce complement, and when the bottleneck migrates.

---

## How to Continue

```bash
cd /root/feedify2
source .venv/bin/activate
uvicorn feedify.api:app --reload --port 8788
```

Read `HANDOVER.md` for full context.
Read `specs/canonical-thesis-v2.md` for the thesis.
Read `AGENTS.md` for the rules.
