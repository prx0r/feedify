"""X adapter + scarcity detector tests. No live API calls."""

from __future__ import annotations

import pytest

from feedify.adapters.x import XAdapter
from feedify.schemas import NormalizedItem
from feedify.services import detector


SAMPLE_TWEET = {
    "id": "2094870937447682508",
    "url": "https://x.com/yeon__/status/2094870937447682508",
    "text": "GlobalFoundries launches cryogenic CMOS for quantum manufacturing at scale",
    "likeCount": 120,
    "viewCount": 8000,
    "retweetCount": 15,
    "replyCount": 4,
    "quoteCount": 2,
    "bookmarkCount": 3,
    "createdAt": "Tue Sep 01 19:32:06 +0000 2026",
    "lang": "en",
    "isReply": False,
    "author": {
        "id": "1444971805618302988",
        "userName": "yeon__",
        "name": "Yeon",
        "followers": 20347,
        "isVerified": True,
    },
}


def _item(**overrides):
    base = {
        "source_type": "x",
        "external_id": "1",
        "title": "t",
        "body": "GlobalFoundries launches cryogenic CMOS for quantum manufacturing",
        "author": "1444971805618302988",
        "metrics": {"author_handle": "yeon__", "author_followers": 20347,
                    "author_verified": True, "likes": 120, "views": 8000},
    }
    base.update(overrides)
    return NormalizedItem(**base)


class TestNormalize:
    def test_author_id_key(self):
        adapter = XAdapter.__new__(XAdapter)
        item = adapter.normalize(SAMPLE_TWEET)
        assert item is not None
        assert item.external_id == "2094870937447682508"
        assert item.author == "1444971805618302988"
        assert item.metrics["author_handle"] == "yeon__"

    def test_raw_preserved(self):
        adapter = XAdapter.__new__(XAdapter)
        item = adapter.normalize(SAMPLE_TWEET)
        assert item is not None
        assert item.raw["text"].startswith("GlobalFoundries")
        assert item.raw["author"]["followers"] == 20347

    def test_missing_id_rejected(self):
        adapter = XAdapter.__new__(XAdapter)
        assert adapter.normalize({"text": "no id"}) is None

    def test_metric_snapshot(self):
        adapter = XAdapter.__new__(XAdapter)
        item = adapter.normalize(SAMPLE_TWEET)
        assert item is not None
        assert item.metrics["likes"] == 120
        assert item.metrics["views"] == 8000
        assert "observed_at" in item.metrics


class TestScarcityDetector:
    def test_fab_claim_implies_gfs(self):
        objects, edges = detector.compile_x(_item(), artifact_id=0)
        assert len(objects) > 0
        ticker_keys = [o.object_key for o in objects if "GFS" in o.object_key.upper()]
        assert len(ticker_keys) > 0

    def test_pq_claim_implies_eth(self):
        item = _item(body="Ethereum targets post-quantum signatures by December 2029, ml-dsa migration")
        objects, edges = detector.compile_x(item, artifact_id=0)
        ticker_keys = [o.object_key for o in objects if "ETH" in o.object_key.upper()]
        assert len(ticker_keys) > 0

    def test_cryogenic_test_implies_form(self):
        item = _item(body="automated cryogenic wafer probing at 4 kelvin for yield data")
        objects, edges = detector.compile_x(item, artifact_id=0)
        ticker_keys = [o.object_key for o in objects if "FORM" in o.object_key.upper()]
        assert len(ticker_keys) > 0

    def test_unrelated_post_filtered_out(self):
        """Low-alpha posts should be filtered out by the scoring formula."""
        item = _item(body="had coffee, thinking about databases")
        objects, edges = detector.compile_x(item, artifact_id=0)
        # Scoring formula should filter this out (no bottleneck relevance, low specificity)
        assert len(objects) == 0

    def test_dispatch_routes_x(self):
        objects, edges = detector.compile_artifact(_item(), artifact_id=0)
        assert len(objects) > 0

    def test_no_duplicate_tickers(self):
        item = _item(body="GlobalFoundries fab foundry manufacturing expansion")
        objects, edges = detector.compile_x(item, artifact_id=0)
        gfs_objects = [o for o in objects if "GFS" in o.object_key.upper()]
        # Should have at most one GFS entity
        assert len(gfs_objects) <= 2  # entity + possibly theory


class TestBudgetGuards:
    def test_unconfigured_adapter(self):
        adapter = XAdapter.__new__(XAdapter)
        adapter.primary_key = ""
        adapter.backup_key = ""
        assert adapter.configured is False

    def test_watchlist_missing_file_returns_empty(self, tmp_path, monkeypatch):
        from feedify.settings import get_settings
        monkeypatch.setenv("GETXAPI_WATCHLIST_PATH", str(tmp_path / "nope.json"))
        get_settings.cache_clear()
        try:
            adapter = XAdapter.__new__(XAdapter)
            assert adapter.watchlist() == []
        finally:
            monkeypatch.undo()
            get_settings.cache_clear()

    def test_zero_balance_short_circuits(self, monkeypatch):
        import asyncio

        adapter = XAdapter.__new__(XAdapter)
        adapter.primary_key = "k"
        adapter.backup_key = ""

        async def fake_balance():
            return 0.0

        monkeypatch.setattr(adapter, "balance", fake_balance)
        assert asyncio.run(adapter.fetch(limit=5)) == []


class TestQuantumFeed:
    def test_quantum_domain_inference(self):
        from feedify.services.detector import infer_domain
        item = _item(body="trapped ion fidelity milestone")
        assert infer_domain(item) == "quantum"

    def test_quantum_feed_seeded(self):
        from feedify.seed import FEEDS
        slugs = [f[0] for f in FEEDS]
        assert "quantum-scarcity" in slugs
