# Backtest Results: Predictions → Evidence

## Summary

| Metric | Count |
|--------|-------|
| Total predictions found | 258 |
| Predictions with connected evidence | 3 |
| Supports | 2 |
| Contradicts | 1 |

## Connected Predictions

### 1. @TweetEdMiller: "The future of robotics might just start with human hands"
- **Predicted**: Feb 2025
- **Evidence**: 2 supporting observations from Feb 2026
- **Verdict**: Prediction validated — 12 months to evidence
- **Lead time**: 12 months

### 2. @Charles_Y_Wu: "The next agent stack will be evolvable"
- **Predicted**: May 2026
- **Evidence**: 2 supporting observations from Aug-Sep 2026
- **Verdict**: Prediction validated — 3-4 months to evidence
- **Lead time**: 3-4 months

### 3. @AmirDGat: ICRA 2025 robotics
- **Predicted**: Mar 2025
- **Evidence**: 1 contradicting observation from Oct 2025
- **Verdict**: Prediction may have been premature
- **Lead time**: N/A (contradicted)

## What This Tells Us

1. **Our graph is too sparse** — Only 3 out of 258 predictions have connected evidence. This is because:
   - Topic-based edges are too coarse
   - We need semantic similarity edges (embedding-based)
   - We need temporal edges (prediction date → evidence date)

2. **The predictions that DO connect show 3-12 month lead times** — This matches our thesis about claim_lead_time

3. **High-alpha accounts make specific, falsifiable predictions** — @TweetEdMiller and @Charles_Y_Wu both made concrete predictions that were validated

## What We Need for Better Backtesting

1. **Embedding-based edges** — Use semantic similarity to connect predictions to evidence, not just shared topics
2. **Temporal edges** — Track prediction date → evidence date → market reaction
3. **Outcome tracking** — For each prediction, track whether it came true and when
4. **Lead time calculation** — How many months between prediction and mainstream recognition

## Top Predictions Worth Tracking

These are the most specific, falsifiable predictions from high-alpha accounts:

| Account | Prediction | Date | Status |
|---------|-----------|------|--------|
| @advaith_sridhar | "Certification/verification is vastly challenging" | Jul 2026 | Tracking |
| @advaith_sridhar | "Merging wafers on each other is the future of GPUs" | Aug 2026 | Tracking |
| @ZitongYang0 | "AI research is a special research area AI itself can deliver progress" | Jan 2026 | Tracking |
| @GenAI_is_real | "Restraint is the moat" | Jul 2026 | Tracking |
| @bravo_abad | "AI may matter most when it stops tuning experiments and starts inventing them" | Sep 2026 | Tracking |
| @KaiyuYang4 | "Bottleneck will move from writing code to reviewing code" | Jun 2025 | Tracking |
| @danfei_xu | "Large models are going to make step changes to robotics" | Sep 2026 | Tracking |
| @tengyanAI | "Cheap electricity that arrives years late is useless" | Aug 2026 | Tracking |
