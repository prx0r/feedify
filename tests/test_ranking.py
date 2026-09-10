from feedify.services.ranking import infer_algorithm_from_prompt


def test_prompt_inference_prefers_alpha_and_actionability():
    weights, filters = infer_algorithm_from_prompt(
        "Only high signal new agent commerce alpha I can build and ship; primary engineers, less noise"
    )
    assert weights["novelty"] > 1
    assert weights["actionability"] > 1
    assert filters["min_score"] >= 0.69
    assert "agents" in filters["domains"]
    assert "commerce" in filters["domains"]
