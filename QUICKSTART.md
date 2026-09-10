# Fresh Agent Quick Start

**If you just arrived at this project, read this first.**

---

## 1. Understand the Project

Feedify is a **knowledge graph compiler**. It takes X/Twitter posts from researchers, classifies them into typed knowledge objects (theories, problems, predictions), builds relationships between objects, and tracks predictions over time.

**Core thesis**: "What does increasing abundance make newly scarce?"

---

## 2. What's Running

- **Feedify v1**: feedify.egoic.ai:8787 (original, untouched)
- **Feedify v2**: v2.feedify.egoic.ai:8788 (rewrite, this repo)

---

## 3. Key Files to Read

1. `HANDOVER.md` — Full project state
2. `specs/canonical-thesis-v2.md` — The thesis
3. `specs/aithesis_people.md` — The 100-account research graph
4. `august/analysis/monthly-summary.md` — What we found from extraction

---

## 4. How to Run

```bash
cd /root/feedify2
source .venv/bin/activate
pytest tests/ -q  # 41 tests pass
uvicorn feedify.api:app --reload --port 8788
```

---

## 5. DB State

```
3,357 artifacts (tweets)
6,101 objects (typed knowledge)
3,622 edges (relationships)
1,043 August tweets from 37 accounts
```

---

## 6. Extraction Bugs to Know

1. **GetXAPI returns max 20 tweets per page** — Always paginate with cursor
2. **Always use date filters** — `since:YYYY-MM-DD until:YYYY-MM-DD`
3. **Without pagination**: @GenAI_is_real shows 24 Aug tweets (actual: 106)

---

## 7. What's Next

1. Run LLM compiler on top 50 tweets
2. Wire interaction tracking
3. Build convergence detection into pipeline
4. Selective 2-year extraction for top 5 accounts

---

## 8. Who to Contact

This project was built in a single session on 2026-09-10. The `SESSION_REVIEW.md` file has the full timeline.
