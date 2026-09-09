# ML Analysis Plan for Feedify

## Based on arxiv Research

### Key Papers

1. **TRACE** (arxiv:2603.12500) — Knowledge graph + LLM for stock prediction
   - 55.1% accuracy, 41.7% return, 2.00 Sharpe
   - Rule-guided graph exploration + LLM reasoning

2. **AlphaPROBE** (arxiv:2602.11917) — DAG-based alpha mining
   - Bayesian Factor Retriever + DAG-aware Factor Generator
   - Outperforms 8 competitive baselines

3. **S³G** (arxiv:2603.24236) — Stock State Space Graph
   - Wavelet transforms + state space models
   - Time-varying graph evolution

4. **Relational Probing** (arxiv:2604.10212) — LLM + graph for stock trends
   - Small language models (0.6B-4B) for relational graph induction
   - Joint training with downstream GAT

5. **LLM-Enhanced Financial KG** (arxiv:2607.10932) — Community-aware signal propagation
   - Dynamic community detection
   - Community Information Surprise (CIS) factor
   - Propagated Information Surprise (PIS) factor

## What We Can Do

### Phase 1: Source Ranking (ML)

**Goal:** Which X accounts produce the most alpha?

**Approach:**
- For each account, track: posts, engagement, reply quality
- Measure: did their posts predict stock moves?
- Output: source_reputation table

**ML Method:** Simple scoring + LLM qualitative assessment

### Phase 2: Signal Prediction (ML)

**Goal:** Predict which signals will lead to stock moves

**Approach:**
- Features: signal_type, domain, score, author_reputation, timing
- Labels: did the stock move after the signal?
- Output: signal_quality scores

**ML Method:** Gradient boosting (XGBoost) or simple neural network

### Phase 3: Convergence Detection (ML)

**Goal:** Detect when multiple labs discuss the same topic

**Approach:**
- Embed recent posts
- Cluster by semantic similarity
- Flag when 2+ independent labs discuss same topic

**ML Method:** Embedding similarity + clustering

### Phase 4: Thesis Evolution (LLM)

**Goal:** Track how theses change over time

**Approach:**
- Store rolling textual summary per person × topic
- Feed previous summary + new posts to LLM
- Ask: "Did their belief materially change?"

**ML Method:** LLM reasoning over text

### Phase 5: Portfolio Optimization (ML)

**Goal:** Optimize position sizing based on thesis alignment

**Approach:**
- Features: thesis_score, financials, convexity, probability
- Labels: historical returns
- Output: optimal weights

**ML Method:** Mean-variance optimization + Kelly criterion

## Priority Order

| Phase | Value | Effort | Priority |
|-------|-------|--------|----------|
| Source Ranking | High | Low | 1 |
| Signal Prediction | High | Medium | 2 |
| Convergence Detection | High | Medium | 3 |
| Thesis Evolution | Medium | Low | 4 |
| Portfolio Optimization | Medium | Medium | 5 |

## Data We Have

- 48 X accounts with 441+ tweets
- 12 stocks with financials
- Knowledge graph (111 nodes, 1127 edges)
- Thesis analyses
- Insider transactions

## What We Need

- Historical stock prices (can get from yfinance)
- Signal timestamps
- Source reputation scores
- Convergence detection results
