# Full Historical Scrape Targets

## Priority 1: Full 2-Year Ingestion (nearly everything)

| Account | August Data | Historical Need | Why |
|---------|-------------|-----------------|-----|
| **Xinyu Ru / Fawkes** | ❌ Not on X | Full fund letters | LEU Oct 2024, LPKF Apr 2026, bottleneck migration |
| **Mike Alkin / @FootnotesFirst** | ✅ 3 tweets | Full 2018-present | Uranium abandoned/mispriced |
| **Arjun Murti / @ArjunNMurti** | ✅ 12 tweets | Full 2024-present | AI electricity demand |
| **Mark Nelson / @energybants** | ✅ 3 tweets | Full 2021-present | Nuclear undervalued |
| **Rob Gramlich** | Not on X | Full articles | Grid demand shift |
| **Brian Janous** | Not on X | Full articles | Data center power |
| **Adam Rodman / Segra** | Not on X | Full fund letters | Uranium institutional |
| **Per Jander / Sprott** | Not on X | Full articles | Uranium fuel cycle |

## Priority 2: Selective Ingestion (long-form only)

| Account | August Data | Historical Need | Why |
|---------|-------------|-----------------|-----|
| **Tae Kim / @firstadopter** | ✅ 1 tweet | Dec 2023 NVDA+VRT+SMCI | Best single validation |
| **Dylan Patel / @dylan522p** | ✅ 9 tweets | July 2023 capacity map | Strongest supply-chain |
| **Gavin Baker / @GavinSBaker** | ✅ 6 tweets | Mar 2023 transformers | Hardware economics |
| **Pierre Ferragu / @p_ferragu** | ❌ 0 tweets | Sep 2021 scaling out | System-scale compute |
| **Jason's Chips / @jasonschips** | ❌ 0 tweets | SUSS early 2026 | Tiny foreign semicap |
| **Doug O'Laughlin** | Not on X | Full podcast archive | Semiconductor sub-layer |
| **Alex Sacerdote / Whale Rock** | Not on X | 13F filings | Hardware decommoditization |

## Priority 3: Daily Ingestion (existing network)

| Account | August Data | Status |
|---------|-------------|--------|
| @aleabitoreddit | ✅ 100 tweets | Already tracked |
| @TheValueist | ✅ 100 tweets | Already tracked |
| @PhotonCap | ✅ 100 tweets | Already tracked |
| @crux_capital_ | ✅ 100 tweets | Already tracked |
| @damnang2 | ✅ 100 tweets | Already tracked |
| @ChipsandWafers | ✅ 62 tweets | Already tracked |

---

## The Meta-Finding

> **Most of the highest-signal people are NOT active on X.**

They're:
- Fund managers (Fawkes, Whale Rock, Segra)
- Analysts (Raymond James, New Street)
- Grid experts (Grid Strategies)
- Industry veterans (Cameco, Microsoft)

**Feedify should ingest:**
1. X posts (daily)
2. Fund letters (monthly)
3. 13F filings (quarterly)
4. Conference presentations (as available)
5. Substack/podcast (weekly)

---

## What to Extract

For each person:
1. **Every stock call** with date and price
2. **Thesis statement** and whether it played out
3. **Accuracy rate** of predictions
4. **Lead time** before market recognition
5. **Price appreciation** after their calls
6. **Cross-domain migration** pattern

---

## The Feed Design

### `precursors.feedify.dev`

**Scoring:**
1. Lead time (months)
2. Specificity (0-10)
3. Causal depth (0-10)
4. Surprise (0-10)
5. Downstream validity (0-10)
6. Sparse output bonus (0-10)
7. Cross-domain migration (0-10)

**Output:**
- Who noticed what, when
- How far ahead of consensus
- What happened next
- Where are they looking now

**That's the highest-signal feed we can build.**
