"""Quantum × AGI scoring engine.

Scores signals based on:
- Role proximity to scaling bottleneck
- Technical specificity
- Reply quality (replies > original posts)
- Obscurity (lower followers = higher signal)
- Novelty
- Vocabulary collision detection (quantum + AI terms)

Key insight: The feed should detect when AI starts materially shortening
the quantum-computer R&D feedback loop.
"""
from __future__ import annotations

from typing import Any

# Priority weights from the user's spec
PRIORITY_WEIGHTS = {
    "S++": 1.0,
    "S+": 0.9,
    "S": 0.8,
    "A+": 0.7,
    "A": 0.6,
    "watch": 0.5,
    "embryonic": 0.4,
}

# Lab relevance (quantum × AGI intersection is highest)
LAB_WEIGHTS = {
    "IonQ": 0.9,
    "Infleqtion": 0.85,
    "IQM": 0.7,
    "Google DeepMind": 0.95,
    "Meta Superintelligence Labs": 0.95,
    "xAI": 0.9,
    "Anthropic": 0.85,
    "OpenAI": 0.9,
    "Axiom": 0.8,
    "DeepMind": 0.9,
    "Meta MSL": 0.9,
}

# Vocabulary signals that indicate regime change
REGIME_CHANGE_PHRASES = [
    "we were surprised", "now scales", "bottleneck", "finally",
    "didn't expect", "works at scale", "previously impossible",
    "our latest run", "decoder", "bigrun", "front lines",
    "self-improving", "breakthrough", "regime change", "phase transition",
    "exponential", "scaling law", "emergent", "capability jump",
    "fault tolerant", "logical error", "qec", "qldpc",
    "rl scaling", "automated research", "self-improving agent",
    "formal verification", "theorem proving", "scientific discovery",
]

# Technical specificity keywords
QUANTUM_TECH = [
    "qec", "qldpc", "decoder", "fault tolerant", "logical error",
    "transmon", "trapped ion", "neutral atom", "photonic",
    "transport overhead", "gate count", "compiler", "microarchitecture",
    "interconnect", "manufacturability", "error correction",
    "logical qubit", "physical qubit", "surface code",
]

AGI_TECH = [
    "rl scaling", "bigrun", "automated research", "self-improving",
    "reasoning", "chain of thought", "formal verification",
    "theorem proving", "scientific discovery", "coding agent",
    "recursive", "agent", "tool use", "reward model",
    "rlhf", "dapo", "grpo", "ppo", "sac",
]


def score_quantum_agi_signal(
    text: str,
    author_handle: str,
    account_info: dict[str, Any],
    is_reply: bool = False,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score a signal for quantum × AGI relevance."""
    text_lower = text.lower()
    metrics = metrics or {}

    # Base score from account priority
    priority = account_info.get("priority", "A")
    priority_score = PRIORITY_WEIGHTS.get(priority, 0.5) * 40  # 0-40 points

    # Lab relevance
    lab = account_info.get("lab", "")
    lab_score = LAB_WEIGHTS.get(lab, 0.5) * 20  # 0-20 points

    # Technical specificity (quantum + AGI terms)
    quantum_hits = sum(1 for t in QUANTUM_TECH if t in text_lower)
    agi_hits = sum(1 for t in AGI_TECH if t in text_lower)
    tech_score = min(20, (quantum_hits + agi_hits) * 4)  # 0-20 points

    # Regime change vocabulary
    regime_hits = sum(1 for p in REGIME_CHANGE_PHRASES if p in text_lower)
    regime_score = min(15, regime_hits * 5)  # 0-15 points

    # Reply bonus (replies > original posts for signal)
    reply_bonus = 10 if is_reply else 0  # 0-10 points

    # Obscurity bonus (lower followers = higher signal)
    followers = metrics.get("author_followers", 10000)
    if followers < 200:
        obscurity_score = 10
    elif followers < 1000:
        obscurity_score = 8
    elif followers < 5000:
        obscurity_score = 5
    elif followers < 10000:
        obscurity_score = 3
    else:
        obscurity_score = 1

    total = priority_score + lab_score + tech_score + regime_score + reply_bonus + obscurity_score
    total = min(100, total)

    # Determine tier
    if total >= 80:
        tier = "S"
    elif total >= 60:
        tier = "A"
    elif total >= 40:
        tier = "B"
    else:
        tier = "C"

    # Check for convergence signals (multiple quantum + AI terms)
    is_convergence = quantum_hits > 0 and agi_hits > 0

    # Determine signal type
    if is_convergence:
        signal_type = "CONVERGENCE"
    elif quantum_hits > agi_hits:
        signal_type = "QUANTUM_LEAD"
    elif agi_hits > quantum_hits:
        signal_type = "AGI_LEAD"
    elif regime_hits > 0:
        signal_type = "REGIME_CHANGE"
    else:
        signal_type = "OBSERVATION"

    return {
        "score": total,
        "tier": tier,
        "signal_type": signal_type,
        "is_convergence": is_convergence,
        "breakdown": {
            "priority": round(priority_score, 1),
            "lab": round(lab_score, 1),
            "technical": round(tech_score, 1),
            "regime": round(regime_score, 1),
            "reply": reply_bonus,
            "obscurity": obscurity_score,
        },
        "quantum_terms": quantum_hits,
        "agi_terms": agi_hits,
        "regime_terms": regime_hits,
    }
