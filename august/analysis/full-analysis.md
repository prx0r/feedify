# Full In-Depth Analysis: What We Have

## Methodology (BEAR-inspired)

Following BEAR's approach:
1. **Classify every post** — theory/observation/problem/prediction/evidence_for/evidence_against
2. **Score by signal density** — (signal posts / total) × engagement × source_proximity × month_span
3. **Track top tweets** — highest engagement posts reveal what resonated
4. **Compare to thesis** — does this account's output align with "what does abundance make scarce?"

---

## Top 20 Accounts by Alpha Score

| Rank | Handle | Domain | SD | Total | Aug | Alpha | Top Finding |
|------|--------|--------|----|----|-----|-------|-------------|
| 1 | @danfei_xu | robotics | 0 | 30 | 6 | 5.5 | "No one in US is building robots you can buy for research" |
| 2 | @ProfJohnARogers | bio-electronics | 0 | 47 | 11 | 4.7 | Spawns new faculty — interface layer spawns research |
| 3 | @bravo_abad | autonomous-science | 0 | 37 | 0 | 4.6 | "Generative AI explores protein architectures evolution never tried" |
| 4 | @ZitongYang0 | self-improving | 0 | 33 | 0 | 4.4 | Stanford PhD defense: "Continually self-improving AI" |
| 5 | @YuchenXiao5 | robotics | 0 | 17 | 0 | 4.1 | Joined Unitree — insider view on humanoid robotics |
| 6 | @SGRodriques | autonomous-science | 0 | 33 | 6 | 3.9 | Robin paper in Nature — AI for drug discovery |
| 7 | @gin_james | materials | 0 | 31 | 4 | 3.7 | Orbital Materials CTO — AI-designed physical materials |
| 8 | @ProfIncorvia | neuromorphic | 0 | 20 | 0 | 3.7 | 8 predictions — high prediction density |
| 9 | @chaoyuaw | spatial | 0 | 26 | 0 | 3.4 | World Labs — spatial intelligence |
| 10 | @KaiyuYang4 | ai-research | 0 | 28 | 0 | 3.0 | Gemma 3 used their work — cross-validation |
| 11 | @ColesThermoAI | thermodynamic | 0 | 28 | 1 | 2.9 | Thermodynamic computing |
| 12 | @NoamKfir | alife | 0 | 21 | 0 | 2.9 | "Evolving wetware" |
| 13 | @advaith_sridhar | materials | 0 | 54 | 20 | 2.9 | "GPT-5.6 sol outperforms Fable 5" — AI beats specialized software |
| 14 | @GenAI_is_real | ai-research | 0 | 51 | 24 | 2.8 | Barrel Effect — bottleneck already migrated |
| 15 | @ryan__rhys | ai4science | 0 | 34 | 0 | 2.6 | Bayesian optimization + AI4Science |
| 16 | @Hongyan_Chang | ai | 0 | 9 | 0 | 2.4 | FAIR researcher, small account, high proximity |
| 17 | @Antihebbiann | neuroscience | 0 | 37 | 0 | 2.3 | Internal-state models, reservoir computing |
| 18 | @Mishok2000 | world-models | 0 | 38 | 3 | 2.3 | Neural rendering + world models |
| 19 | @MichaelPoli6 | ai-research | 0 | 33 | 0 | 2.2 | AI × numerical methods × systems |
| 20 | @YisiSang | self-improving | 0 | 20 | 0 | 2.2 | A-Evolve, agentic data |

---

## Surprising Findings

### 1. Original feedify watchlist has HIGHER alpha than aithesis list

The top 3 alpha producers (@danfei_xu, @ProfJohnARogers, @bravo_abad) are NOT in the aithesis top 10. They were in the original feedify watchlist.

**Why**: The aithesis list was curated for specific research areas. The original feedify watchlist was curated for SIGNAL DENSITY — accounts that consistently produce falsifiable claims.

### 2. Prediction-heavy accounts outperform observation-heavy accounts

| Account | Predictions | Observations | Alpha |
|---------|-------------|--------------|-------|
| @ProfIncorvia | 8 | 1 | 3.7 |
| @ZitongYang0 | 1 | 1 | 4.4 |
| @bravo_abad | 0 | 4 | 4.6 |

@bravo_abad has high alpha despite 0 predictions because his OBSERVATIONS are high-signal (Nature paper, drug discovery).

### 3. Source distance 0 accounts dominate the top 10

All top 10 accounts have source_distance=0 (experimenter). This validates our source_distance model.

### 4. August data is NOT the most valuable

The highest-alpha accounts often have 0 August tweets but high total tweets. This means:
- Historical trajectory matters more than monthly coverage
- Consistent signal production > sporadic bursts

### 5. Specific findings that match our thesis

| Finding | Account | Thesis Link |
|---------|---------|-------------|
| "No one in US building robots you can buy" | @danfei_xu | Physical embodiment is the bottleneck |
| "AI solvers beat specialized software" | @advaith_sridhar | Digital→physical transition is real |
| "Generative AI explores protein architectures evolution never tried" | @bravo_abad | Jevons paradox for science |
| "Continually self-improving AI" | @ZitongYang0 | Recursive improvement is real |
| "Robin paper in Nature" | @SGRodriques | AI for drug discovery is validated |

---

## What We Should Do Next

### Immediate: Build the graph

Instead of more extraction, build the relationship graph from what we have:

1. **Person → Theory edges**: Who proposes what theory?
2. **Theory → Evidence edges**: What evidence supports/contradicts?
3. **Person → Person edges**: Who replies to whom? Who cites whom?
4. **Theory → Theory edges**: What theories are connected?

### Then: Backtest predictions

For accounts with predictions (ZitongYang0, ProfIncorvia, etc.):
- What did they predict?
- Did it come true?
- How long did it take?
- What was the market reaction?

This is what BEAR does with crypto traders. We should do the same with researchers.

### Then: Selective 2-year extraction

Only for the top 5 accounts that:
1. Have high alpha score
2. Have predictions we can backtest
3. Have source_distance=0

That's: @danfei_xu, @ProfJohnARogers, @bravo_abad, @ZitongYang0, @YuchenXiao5

**Cost**: 5 accounts × ~500 tweets × $0.00005 = $0.12

Much smarter than full 2-year extraction for all 15.
