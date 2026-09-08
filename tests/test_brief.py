"""Brief clustering + price tests. Price fetches are fixture-driven (no network)."""

from __future__ import annotations

import pytest

from feedify.services import brief
from feedify.services.brief import alpha_score, build_brief, cluster_items, synthesize_brief


def _item(title, score=0.9, tags=None, **kw):
    d = {"title": title, "summary": "s", "why_it_matters": "w",
         "score": score, "tags": tags or [], "signal_type": "SCARCITY_SHOCK",
         "domain": "quantum", "url": "http://x/y"}
    d.update(kw)
    return d


class TestClustering:
    def test_near_dupes_merge(self):
        items = [
            _item("IonQ debuts Superion 256 qubit system https://t.co/abc #IonQ"),
            _item("IonQ debuts Superion 256 qubit system https://t.co/xyz @IonQ_Inc"),
            _item("Quantinuum Oracle partnership announced"),
        ]
        groups = cluster_items(items)
        assert len(groups) == 2
        assert len(groups[0]) == 2

    def test_distinct_stay_split(self):
        items = [_item("IonQ debuts Superion 256"), _item("FormFactor cryogenic wafer probing")]
        assert len(cluster_items(items)) == 2

    def test_empty(self):
        assert cluster_items([]) == []


class TestAlphaScore:
    def test_corroboration_bonus(self):
        moves = {}
        single = [_item("IonQ news", score=0.9)]
        double = [_item("IonQ news A", score=0.9), _item("IonQ news A!", score=0.9)]
        assert len(cluster_items(double)) == 1
        s1, _ = alpha_score(single, moves)
        s2, _ = alpha_score(cluster_items(double)[0], moves)
        assert s2 > s1

    def test_unmoved_bonus_needs_corroboration(self):
        moves = {"IONQ": {"pct_1d": 0.5}}
        lone = [_item("x", tags=["ionq"])]
        s, reasons = alpha_score(lone, moves)
        assert not any(r.startswith("unmoved") for r in reasons)

    def test_ticker_extraction(self):
        story = [_item("x", tags=["x", "scarcity-shock", "gfs"])]
        s, reasons = alpha_score(story, {"GFS": {"pct_1d": 5.0}})
        assert s == pytest.approx(0.9)


class TestBrief:
    def _feed(self):
        from feedify.models import Feed
        return Feed(slug="q", name="Q", prompt="quantum", weights={}, filters={})

    def test_build_orders_by_alpha(self, monkeypatch):
        import feedify.services.brief as b

        items = [_item("lone story", score=0.82),
                 _item("big story A", score=0.8),
                 _item("big story A!", score=0.8)]
        monkeypatch.setattr(b, "get_ranked_feed", lambda *a, **k: items)
        monkeypatch.setattr(b.prices, "get_moves", lambda t: {})
        out = build_brief(None, self._feed(), limit=5)
        assert out["story_count"] == 2
        assert out["stories"][0]["sources"] == 2

    def test_synthesize_readable(self):
        brief_data = {"stories": [
            {"title": "T", "score": 0.95, "tickers": ["GFS"],
             "moves": {"GFS": {"pct_1d": 0.3}}, "sources": 3,
             "reasons": ["corroborated:3", "unmoved:GFS"]},
        ]}
        text = synthesize_brief(brief_data)
        assert "GFS" in text and "+0.3%" in text and "corroborated:3" in text


class TestPrices:
    def test_stooq_parse(self, monkeypatch):
        import feedify.services.prices as p

        class Resp:
            text = ('Date,Open,High,Low,Close,Volume\n'
                    '2026-09-07,10,11,9,10,1000\n'
                    '2026-09-08,10,11,9,10.5,1000\n')

            def raise_for_status(self):
                pass

        monkeypatch.setattr(p.httpx, "get", lambda *a, **k: Resp())
        p._cache.clear()
        moves = p.get_moves(["GFS", "NOPE"])
        assert moves["GFS"]["price"] == 10.5
        assert moves["GFS"]["pct_1d"] == 5.0
        assert "NOPE" not in moves

    def test_cache_serves_stale_on_error(self, monkeypatch):
        import feedify.services.prices as p
        p._cache.clear()
        p._cache["stooq:GFS"] = (9999999999.0, {"GFS": {"price": 1.0}})

        def boom(*a, **k):
            raise RuntimeError("down")

        monkeypatch.setattr(p.httpx, "get", boom)
        assert p.get_moves(["GFS"]) == {"GFS": {"price": 1.0}}

    def test_unmoved_threshold(self, monkeypatch):
        import feedify.services.prices as p
        monkeypatch.setattr(p, "get_moves",
                            lambda t: {"A": {"pct_1d": 0.5}, "B": {"pct_1d": 9.0}})
        assert p.unmoved(["A", "B"]) == ["A"]
