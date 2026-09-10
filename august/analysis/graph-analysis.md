# Graph Analysis: Embedding-Based Connections

## Graph State

| Metric | Count |
|--------|-------|
| Objects | 3,548 |
| Edges | 584 |
| Supports | 196 |
| Contradicts | 25 |
| Related_to | 359 |
| Avg edge weight | 0.52 |
| Predictions connected | 140/140 |

## What the Graph Reveals

### 1. Strongest Prediction-Evidence Pairs

| Prediction | Author | Date | Supports | Contradicts | Avg Weight |
|-----------|--------|------|----------|-------------|------------|
| AI4Science paper published | @ShuiwangJi | Jul 2025 | 3 | 0 | 0.67 |
| VLN survey | @YanyuanQiao | Jul 2024 | 3 | 0 | 0.64 |
| Unitree robotics chapter | @YuchenXiao5 | Jun 2024 | 3 | 0 | 0.58 |
| Autogenesis evolvable agents | @Charles_Y_WU | May 2026 | 3 | 0 | 0.55 |
| Neural data science datasets | @Antihebbiann | Jul 2023 | 3 | 0 | 0.53 |

### 2. Key Finding: Predictions Cluster by Domain

The embedding edges show that predictions cluster by domain:
- **Robotics**: @YuchenXiao5, @danfei_xu, @TweetEdMiller → evidence from robotics papers
- **AI4Science**: @ShuiwangJi, @SGRodriques, @Ryan__Rhys → evidence from Nature papers
- **Neuroscience**: @Antihebbiann, @ProfIncorvia → evidence from neuroscience research
- **Materials**: @ProfJohnARogers, @advaith_sridhar → evidence from materials papers

### 3. Contradictions Are Rare but Valuable

Only 25 contradictions in 584 edges (4.3%). This suggests:
- Most predictions in our dataset are either validated or unconnected
- Contradictions are genuinely informative — they flag predictions that failed

## Top 10 Predictions to Track

Based on connection quality and thesis alignment:

| Rank | Author | Prediction | Date | Why Track |
|------|--------|-----------|------|-----------|
| 1 | @Charles_Y_WU | "Next agent stack will be evolvable" | May 2026 | Autogenesis is real |
| 2 | @advaith_sridhar | "Certification/verification is vastly challenging" | Jul 2026 | Permission scarcity thesis |
| 3 | @ZitongYang0 | "AI research is a special research area" | Jan 2026 | Self-improvement thesis |
| 4 | @GenAI_is_real | "Restraint is the moat" | Jul 2026 | Bottleneck migration thesis |
| 5 | @bravo_abad | "AI stops tuning experiments, starts inventing them" | Sep 2026 | Experimental scarcity thesis |
| 6 | @KaiyuYang4 | "Bottleneck moves from writing to reviewing code" | Jun 2025 | Verification economy thesis |
| 7 | @danfei_xu | "Large models make step changes to robotics" | Sep 2026 | Embodiment thesis |
| 8 | @tengyanAI | "Cheap electricity arriving years late is useless" | Aug 2026 | Permission scarcity thesis |
| 9 | @advaith_sridhar | "Merging wafers on each other is the future of GPUs" | Aug 2026 | Cross-world monopoly thesis |
| 10 | @TweetEdMiller | "Knowledge valued when participants are AI agents" | Jul 2026 | Verification economy thesis |

## Next Steps

1. **Monitor these 10 predictions** — Set up alerts for when evidence appears
2. **Build temporal edges** — Track prediction date → evidence date → market reaction
3. **Selective 2-year extraction** — For the 5 highest-alpha accounts to deepen the graph
