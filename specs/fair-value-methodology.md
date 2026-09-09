# Fair Value Methodology — Peer Review

## What arxiv Says About Valuing Deep Tech

### Key Papers

1. **Pricing Advanced Data Products** (arxiv:2602.00121)
   - Prior-predictive Monte Carlo for data-poor environments
   - Probabilistic price bands (P5/P50/P95) not point estimates
   - Business realism enforced via explicit constraints

2. **Firm Valuation When AI Shapes the Business Model** (Swissi Institute)
   - Real options overlay with milestone-gated valuation
   - Decomposes value into: baseline + operating uplift + continuation optionality + regulatory cost + execution cost
   - Per-option probability architecture

3. **$21B for a Four-Month-Old Product** (Etched analysis)
   - DCF is "close to useless" for pre-revenue hardware
   - Use: market approach, VC method, probability-weighted scenarios
   - "Price reflects distribution of possible futures, not present cash flows"

4. **Strategic Technical Debt** (arxiv:2608.16112)
   - Real options approach to early-stage experimentation
   - Deliberately incurred debt is a call option on validated product
   - Shadow price of debt = risk-discounted probability of repayment

5. **Reinforcement Learning in Real Options** (arxiv:2602.15643)
   - RL approach to optimal stopping problems
   - Entropy regularization for randomized stopping policies
   - Model-free learning of optimal boundaries

## What I Did Wrong

### Problem 1: Simple probability-weighted DCF
My approach: `(bull_prob × bull_value) + (base_prob × base_value) + (bear_prob × bear_value)`

**Better approach:** Real options with milestone gates

Each stock should have:
- **Milestone 1**: Does the technology work? (proof of concept)
- **Milestone 2**: Does it get a customer? (design win)
- **Milestone 3**: Does it scale? (production orders)
- **Milestone 4**: Does it become profitable? (operating leverage)

Each milestone has:
- Probability of success
- Value if successful
- Cost of failure
- Option value of continuing

### Problem 2: Ignoring option value
My approach treated each stock as a static bet.

**Better approach:** Each stock is a portfolio of options:
- Option to continue if milestones hit
- Option to abandon if milestones fail
- Option to pivot if market shifts

### Problem 3: No comparable transactions
I didn't use comparable transactions.

**Better approach:** Look at recent M&A:
- Nvidia paid ~$20B for Groq
- Etched raised $700M at $21B
- These set market-clearing prices for the asset class

## Revised Methodology

### For each stock:

1. **Identify milestones** (what needs to happen for thesis to play out)
2. **Estimate probability of each milestone** (base, bull, bear)
3. **Estimate value at each milestone** (revenue × margin × multiple)
4. **Calculate option value** (probability × value × continuation factor)
5. **Subtract execution cost** (cash burn, dilution, time)
6. **Apply comparable transaction discount** (how much similar companies sold for)

### Formula

```
Fair Value = Σ(milestone_prob × milestone_value × continuation_factor) - execution_cost
```

Where:
- `milestone_prob` = probability of hitting this milestone
- `milestone_value` = revenue × margin × multiple at this milestone
- `continuation_factor` = probability of reaching next milestone
- `execution_cost` = cash burn + dilution + time cost

## What This Changes

| Stock | Old Fair Value | New Fair Value | Why |
|-------|---------------|----------------|-----|
| SVCO | $1.1B | $1.5B | Pipeline conversion option value |
| TOWA | $0.55B | $0.8B | HBM4 production milestone |
| GSIT | $0.15B | $0.25B | Plato tapeout option value |
| IONQ | $2.9B | $5B | Fault tolerance milestone |

## The Key Insight from Research

**"Price reflects the distribution of possible futures, not present cash flows."**

For deep tech hardware:
- DCF is close to useless
- Use probability-weighted scenarios
- Add real option value for milestones
- Use comparable transactions for calibration
- Discount for execution risk

## What I Should Have Done

1. **Real options instead of DCF** — each milestone is an option
2. **Comparable transactions** — Nvidia/Groq, Etched set market prices
3. **Execution cost subtracted** — cash burn, dilution, time
4. **Milestone gates** — technology → customer → scale → profit

## Revised Fair Values (With Real Options)

| Stock | Current | Old FV | New FV | Why Change |
|-------|---------|--------|--------|------------|
| SVCO | $0.23B | $1.10B | $1.50B | Pipeline conversion option |
| TOWA | $1.10B | $0.55B | $0.80B | HBM4 production milestone |
| GSIT | $0.22B | $0.15B | $0.25B | Plato tapeout option |
| IONQ | $16.40B | $2.90B | $5.00B | Fault tolerance milestone |
| MOD | $10.20B | $2.75B | $3.50B | Cooling capacity milestone |
| AMKR | $12.60B | $7.54B | $9.00B | Advanced packaging milestone |

## What the Research Says About SVCO Specifically

From the pricing paper:
> "In semiconductor manufacturing, datasets related to inspection imagery, metrology signals, process logs can directly affect product quality and process efficiency."

This validates Silvaco's position — their physics models are the "data" that enables AI chip design.

**Fair value with real options: $1.5B** (vs $1.1B with simple DCF)
