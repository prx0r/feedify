# The Canonical Thesis v2.0: Scarcity Migration

**Date**: 2026-09-10
**Status**: Active — replaces previous thesis

---

## Core Equation

$$
\boxed{
\text{What does increasing abundance make newly scarce?}
}
$$

AGI makes cognition, search, design, coding, simulation and hypothesis generation abundant. That abundance creates **induced demand for their complements**. Those complements then become bottlenecks, attract rents, trigger investment, eventually get relieved, and push scarcity somewhere else.

---

## The Moving Scarcity Surface

```
INTELLIGENCE BECOMES ABUNDANT
          ↓
hypotheses/designs/code become abundant
          ↓
VERIFICATION becomes scarce
          ↓
verification gets automated
          ↓
PHYSICAL EXPERIMENTS become scarce
          ↓
experiments scale
          ↓
INSTRUMENTS / LAB CAPACITY / MATERIALS become scarce
          ↓
manufacturing scales
          ↓
ENERGY / GRID / PERMISSIONS become scarce
          ↓
those expand
          ↓
new physical / legal / geological / biological bottleneck
```

---

## Jevons Paradox for Science

AI reduces cost of generating plausible designs by 10,000×. You do NOT necessarily make physical experimentation 10,000× less valuable. You make it vastly **more valuable**, because now there are a million things worth testing.

$$
\frac{\partial \text{demand for physical validation}}
{\partial \text{AI capability}}
>0
$$

---

## Cross-World Monopolies

Investments conditional on one architecture winning:

$$
P(\text{payoff}|\text{one architecture wins})
$$

vs companies whose demand rises under six or eight futures:

$$
\text{Cross-world exposure}
=
\sum_s P(s)\times \mathbf{1}[\text{needed in state }s]
$$

---

## The AI-to-Atoms Interface

Three regimes:

```
DIGITAL          → software, models, reasoning, simulation, design
INTERFACE        → measurement, verification, robotics, instrumentation, controls, sensors, metrology
PHYSICAL         → atoms, cells, energy, manufacturing, land, materials, biology
```

AGI drives the marginal cost of the top layer toward zero much faster than the bottom. The **interface layer** becomes extraordinarily important.

---

## Moving Scarcity Surface (formal)

$$
B_i
=
\frac{
\text{induced demand}
\times \text{indispensability}
\times \text{replacement time}
\times \text{permission friction}
}{
\text{available capacity}
+ \text{substitutes}
+ \text{inventory}
}
$$

Model $\frac{dB_i}{dt}$ not just $B_i$.

---

## Bottleneck Alpha

$$
\text{Bottleneck alpha}
=
\text{identify bottleneck}
-
\text{identify supply response}
$$

---

## Bottleneck Derivative

What becomes constrained **if the currently constrained item succeeds in scaling?**

Metrology is a derivative on HBM success. LPKF is a derivative on packaging success.

---

## Permission Scarcity

$$
\text{Deliverable MW}
=
\text{announced MW}
\times P(\text{site})
\times P(\text{interconnect})
\times P(\text{transformer})
\times P(\text{generation})
\times P(\text{permit})
$$

---

## Three Clocks

Every event carries:
- $t_c$ = capability time
- $t_d$ = deployment time  
- $t_f$ = cash-flow time

---

## Surprise-Based Alpha

$$
Surprise(e_t)
=
e_t - E[e_t|W_{t-1}]
$$

$$
\Delta P(W)
\propto Surprise(e_t) \times Credibility(e_t)
$$

Not: how impressive headline sounds.

---

## Irreducibility

$$
Irreducibility(x)
=
Cost(\text{obtain genuine observation})
-
Cost(\text{synthetically approximate it})
$$

High-irreducibility datasets become increasingly valuable.

---

## World-State Consistency Arbitrage

For each stock, infer the world its price requires. Find pairs/clusters whose valuations require contradictory futures.

$$
W_1 \land W_2 \land W_3 \ldots \text{ test for consistency}
$$

---

## Researcher Alpha

$$
ResearcherAlpha =
\frac{
Novelty \times FutureCentrality \times EmpiricalGrounding \times LeadTime
}
{AudienceSize^\alpha}
$$

---

## Master Equation

$$
Alpha_i=
\sum_{s,t}
\underbrace{(P_{ours}(s,t)-P_{market}(s,t))}_{belief\ gap}
\times \underbrace{\Delta CF_i(s,t)}_{cashflow\ effect}
\times \underbrace{X_i(s)}_{cross-world\ exposure}
\times \underbrace{B_i(s,t)}_{scarcity}
\times \underbrace{R_i(t)}_{irreducibility}
- \underbrace{C_i(t)}_{crowdedness}
$$

---

## Top 5 Research Programs

1. **Scarcity Migration Engine** — For every capability shock: what becomes abundant → what complement receives induced demand → can supply respond → what's the next constraint
2. **AI→Atoms Index** — Universe around test + measurement + characterization + automation + control + verification + certification
3. **World-State Consistency Arbitrage** — Reverse-DCF thousands, find contradictory implied futures
4. **Real Usage → Economic Destruction Graph** — OpenRouter tokens → task automation → affected labor → affected companies → induced complement demand
5. **Technical Half-Life / Obsolescence Short Engine** — Estimate survival of business models vs valuation duration

---

## Key Companies to Deep-Dive

**Interface layer (AI→Atoms):**
LPKF, Chroma ATE, FormFactor, Keysight, Oxford Instruments, Tecan, KLA, Nova, Camtek, Advantest, Bruker, UL Solutions

**Permission scarcity:**
Grid operators, FERC, transformer manufacturers, certification bodies

**Experimental validation:**
Scientific instrumentation, lab automation, assay platforms, bioreactors

---

## Feedify's Role

Feedify becomes the **sensory nervous system** of the world-state model.

Feeds:
```
/bottlenecks/experimental-characterization
/bottlenecks/cpo-testing
/bottlenecks/quantum-control
/bottlenecks/grid-permissions
/capabilities/robotics
/capabilities/biological-programming
/obsolescence/it-services
/obsolescence/seat-saas
/worldstate/ai-to-atoms
/people/frontier-hidden-nodes
```

Every observation = Bayesian update, not another post in a feed.

---

## The One Sentence

> **Feedify is not an AI RSS reader.**
>
> **Feedify is the sensory nervous system for a moving scarcity surface — tracking what becomes abundant, what that makes scarce, who owns the scarce complement, and when the bottleneck migrates.**
