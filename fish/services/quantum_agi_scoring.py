"""Quantum × AGI scoring engine — updated with acceleration thesis priorities.

New scoring formula:
  Signal = 0.30(Role proximity) + 0.25(Technical specificity) + 0.20(Cross-domain leverage)
         + 0.15(Reply quality) + 0.10(Obscurity)

Key changes:
- Employment proximity > follower count
- Domain competence > virality
- Reply quality > original posts
- Scarcity of source > popularity
"""
from __future__ import annotations

from typing import Any

# Priority weights
PRIORITY_WEIGHTS = {
    "S++": 1.0,
    "S+": 0.9,
    "S": 0.8,
    "A+": 0.7,
    "A": 0.6,
    "watch": 0.5,
    "embryonic": 0.4,
}

# Lab relevance
LAB_WEIGHTS = {
    "IonQ": 0.9, "Infleqtion": 0.85, "IQM": 0.7,
    "Google DeepMind": 0.95, "Meta Superintelligence Labs": 0.95,
    "Meta MSL": 0.95, "Meta/FAIR": 0.9, "xAI": 0.9,
    "Anthropic": 0.85, "OpenAI": 0.9, "Axiom": 0.8, "DeepMind": 0.9,
    "Recursive": 0.95, "Architect Labs": 0.95, "Normal Computing": 0.9,
    "Extropic": 0.85, "Lightmatter": 0.85, "Periodic Labs": 0.95,
    "Lila Sciences": 0.9, "Diffuse Bio": 0.85, "Discovered Materials": 0.85,
    "Proxima Fusion": 0.8, "PhysicsX": 0.85, "Orbital Industries": 0.9,
    "Harmonic": 0.85, "Skild AI": 0.9, "Etched": 0.9,
    "Chai Discovery": 0.85, "PsiQuantum": 0.8, "CuspAI": 0.85,
    "Project Prometheus": 0.9, "Accelerated Understanding": 0.85,
    "Physical Intelligence": 0.9, "Genesis AI": 0.85, "FutureHouse": 0.85,
}


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

    # 1. Role proximity (0-30 points)
    priority = account_info.get("priority", "A")
    role_score = PRIORITY_WEIGHTS.get(priority, 0.5) * 30

    # 2. Technical specificity (0-25 points)
    all_tech = [
        "qec", "qldpc", "decoder", "fault tolerant", "logical error",
        "transmon", "trapped ion", "neutral atom", "photonic",
        "rl scaling", "bigrun", "automated research", "self-improving",
        "reasoning", "chain of thought", "formal verification", "lean",
        "agent", "tool use", "coding agent", "theorem proving",
        "silicon", "asic", "rtl", "verification", "compiler",
        "materials", "synthesis", "experiment", "laboratory",
        "protein", "molecular", "drug", "assay",
        "robot", "policy", "embodiment", "simulation",
        "interconnect", "photonics", "optics",
    ]
    tech_hits = sum(1 for t in all_tech if t in text_lower)
    tech_score = min(25, tech_hits * 3)

    # 3. Cross-domain leverage (0-20 points)
    quantum_terms = {"qec", "qldpc", "decoder", "fault tolerant", "qubit", "trapped ion", "photonic"}
    agi_terms = {"rl", "reasoning", "agent", "self-improving", "automated research", "formal verification"}
    hardware_terms = {"silicon", "asic", "rtl", "compiler", "interconnect", "photonics"}
    science_terms = {"materials", "synthesis", "experiment", "laboratory", "protein", "molecular"}
    robotics_terms = {"robot", "policy", "embodiment", "simulation", "manipulation"}

    q_hits = sum(1 for t in quantum_terms if t in text_lower)
    a_hits = sum(1 for t in agi_terms if t in text_lower)
    h_hits = sum(1 for t in hardware_terms if t in text_lower)
    s_hits = sum(1 for t in science_terms if t in text_lower)
    r_hits = sum(1 for t in robotics_terms if t in text_lower)

    domains_present = sum(1 for hits in [q_hits, a_hits, h_hits, s_hits, r_hits] if hits > 0)
    cross_score = min(20, (domains_present - 1) * 10) if domains_present > 1 else 0

    # 4. Reply quality (0-15 points)
    reply_score = 15 if is_reply else 0

    # 5. Obscurity (0-10 points)
    followers = metrics.get("author_followers", 10000)
    if followers < 100:
        obscurity_score = 10
    elif followers < 500:
        obscurity_score = 8
    elif followers < 2000:
        obscurity_score = 6
    elif followers < 5000:
        obscurity_score = 4
    elif followers < 10000:
        obscurity_score = 2
    else:
        obscurity_score = 1

    total = role_score + tech_score + cross_score + reply_score + obscurity_score
    total = min(100, total)

    if total >= 80:
        tier = "S"
    elif total >= 60:
        tier = "A"
    elif total >= 40:
        tier = "B"
    else:
        tier = "C"

    if domains_present >= 3:
        signal_type = "CONVERGENCE"
    elif q_hits > 0 and a_hits > 0:
        signal_type = "CROSS_DOMAIN"
    elif q_hits > a_hits:
        signal_type = "QUANTUM_LEAD"
    elif a_hits > q_hits:
        signal_type = "AGI_LEAD"
    elif tech_hits > 3:
        signal_type = "TECHNICAL"
    else:
        signal_type = "OBSERVATION"

    return {
        "score": total,
        "tier": tier,
        "signal_type": signal_type,
        "breakdown": {
            "role": round(role_score, 1),
            "technical": round(tech_score, 1),
            "cross_domain": round(cross_score, 1),
            "reply": reply_score,
            "obscurity": obscurity_score,
        },
        "tech_terms": tech_hits,
        "domains_present": domains_present,
    }
