from fish.schemas import NormalizedItem
from fish.services.detector import compile_artifact


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
    objects, edges = compile_artifact(item, artifact_id=0)
    assert len(objects) > 0
    pick = next((o for o in objects if o.kind == "pick"), objects[0])
    assert pick.domain == "ios"
    assert pick.confidence > 0.7


def test_glama_is_new_capability():
    item = NormalizedItem(
        source_type="glama",
        external_id="a/b",
        title="Marketplace MCP",
        body="Search retail marketplace inventory and checkout",
        metrics={"official": True, "categories": ["E-commerce"]},
    )
    objects, edges = compile_artifact(item, artifact_id=0)
    assert len(objects) > 0
    tech = objects[0]
    assert tech.kind == "technology"
    assert tech.domain == "commerce"
    assert tech.confidence >= 0.7
