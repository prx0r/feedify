from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from feedify.models import Feed, Object
from feedify.services import prices
from feedify.services.feeds import get_ranked_feed

_URL_RE = re.compile(r"https?://\S+|t\.co/\S+")
_HANDLE_RE = re.compile(r"@\w+")
_WS_RE = re.compile(r"\s+")

_STOP = {
    "the", "and", "our", "with", "from", "that", "this", "for", "are",
    "have", "will", "today", "just", "now", "new", "more", "your",
}


def story_tokens(title: str) -> set[str]:
    text = _URL_RE.sub(" ", title or "")
    text = _HANDLE_RE.sub(" ", text)
    text = re.sub(r"#", "", text)
    return {w for w in re.findall(r"[a-z0-9][a-z0-9'-]{2,}", text.lower())
            if w not in _STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster_items(items: list[dict[str, Any]], threshold: float = 0.35) -> list[list[dict[str, Any]]]:
    parent = list(range(len(items)))
    toks = [story_tokens(i.get("title", "")) for i in items]

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if find(i) != find(j) and jaccard(toks[i], toks[j]) >= threshold:
                parent[find(i)] = find(j)
    groups: dict[int, list[dict]] = {}
    for i, item in enumerate(items):
        groups.setdefault(find(i), []).append(item)
    return sorted(groups.values(), key=lambda g: -max(float(x.get("score", 0)) for x in g))


def alpha_score(story: list[dict[str, Any]], moves: dict[str, dict]) -> tuple[float, list[str]]:
    best = max(story, key=lambda x: float(x.get("score", 0)))
    base = float(best.get("score", 0))
    reasons = [f"base:{base:.2f}"]
    tickers: list[str] = []
    for item in story:
        for t in item.get("tags", []) or []:
            tu = str(t).upper()
            if tu not in tickers and tu.isalpha() and len(tu) <= 5:
                tickers.append(tu)
    score = base
    if len(story) > 1:
        bonus = min(0.18, 0.06 * (len(story) - 1))
        score += bonus
        reasons.append(f"corroborated:{len(story)}")
    flat = [t for t in tickers if t in moves and abs(moves[t]["pct_1d"]) < 2.0]
    if flat and len(story) > 1:
        score += 0.06
        reasons.append(f"unmoved:{','.join(flat[:4])}")
    return round(score, 4), reasons


def build_brief(session: Session, feed: Feed, limit: int = 10) -> dict[str, Any]:
    items = get_ranked_feed(session, feed, limit=100)
    stories = cluster_items(items)
    tickers = sorted({t.upper() for s in stories for i in s
                      for t in (i.get("tags") or [])
                      if str(t).upper().isalpha() and len(str(t)) <= 5
                      and str(t).upper() not in {"X", "RSS"}})
    moves = prices.get_moves(tickers)
    ranked = []
    for story in stories:
        best = max(story, key=lambda x: float(x.get("score", 0)))
        score, reasons = alpha_score(story, moves)
        story_tickers = sorted({t.upper() for i in story for t in (i.get("tags") or [])
                                if str(t).upper() in moves})
        ranked.append({
            "title": best.get("title"),
            "summary": best.get("summary"),
            "score": score,
            "reasons": reasons,
            "sources": len(story),
            "tickers": story_tickers,
            "moves": {t: moves[t] for t in story_tickers},
            "domain": best.get("domain"),
        })
    ranked.sort(key=lambda s: -s["score"])
    return {
        "feed": feed.slug,
        "stories": ranked[:limit],
        "story_count": len(ranked),
        "item_count": len(items),
        "prices_asof": "mixed snapshots, see per-ticker asof",
    }


def synthesize_brief(brief: dict[str, Any]) -> str:
    lines = [f"Top {len(brief['stories'])} stories by alpha score:"]
    for i, s in enumerate(brief["stories"], 1):
        moves = " ".join(f"{t}{m['pct_1d']:+.1f}%" for t, m in s["moves"].items())
        lines.append(f"{i}. [{s['score']:.2f}] {s['title']}")
        if s["tickers"]:
            lines.append(f"   tickers: {' '.join(s['tickers'])} | 1d: {moves or 'no data'}")
        lines.append(f"   sources: {s['sources']} | {'; '.join(s['reasons'])}")
    return "\n".join(lines)
