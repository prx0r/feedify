from fish.schemas import NormalizedItem
from fish.services.detector import calculate_base_score, detect


def test_trustmrr_breakout_signal():
    item = NormalizedItem(
        source_type="trustmrr",
        external_id="x",
        title="TinyCo",
        metrics={
            "last30d_revenue_cents": 2500000,
            "growth30d": 35,
            "category": "mobile-apps",
            "on_sale": False,
        },
    )
    signals = detect(item)
    breakout = next(s for s in signals if s.signal_type == "REVENUE_ACCELERATION")
    assert breakout.domain == "ios"
    assert breakout.actionability > 0.8
    assert calculate_base_score(breakout) > 0.7


def test_glama_is_new_capability():
    item = NormalizedItem(
        source_type="glama",
        external_id="a/b",
        title="Marketplace MCP",
        body="Search retail marketplace inventory and checkout",
        metrics={"official": True, "categories": ["E-commerce"]},
    )
    signal = detect(item)[0]
    assert signal.signal_type == "NEW_CAPABILITY"
    assert signal.domain == "commerce"
    assert signal.source_proximity >= 0.9
