from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from math import log10
from pathlib import Path
from typing import Iterable

from fish.schemas import NormalizedItem, ObjectDraft, EdgeDraft


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


_WATCHLIST_CACHE: dict[str, dict] | None = None


def _load_watchlist() -> dict[str, dict]:
    """Load watchlist and build handle → source_distance lookup."""
    global _WATCHLIST_CACHE
    if _WATCHLIST_CACHE is not None:
        return _WATCHLIST_CACHE
    try:
        path = Path(__file__).parent.parent.parent / "config" / "acceleration_watchlist.json"
        entries = json.loads(path.read_text())
        _WATCHLIST_CACHE = {}
        for entry in entries:
            handle = entry.get("handle", "").lower()
            if handle:
                _WATCHLIST_CACHE[handle] = entry
        return _WATCHLIST_CACHE
    except Exception:
        _WATCHLIST_CACHE = {}
        return _WATCHLIST_CACHE


def get_source_distance(handle: str) -> int:
    """Get source_distance for a handle. 0=experimenter, 5=influencer."""
    watchlist = _load_watchlist()
    entry = watchlist.get(handle.lower(), {})
    return entry.get("source_distance", 3)  # default to analyst


def get_source_proximity(handle: str) -> float:
    """Convert source_distance to source_proximity score."""
    d = get_source_distance(handle)
    return {0: 0.95, 1: 0.85, 2: 0.7, 3: 0.5, 4: 0.3, 5: 0.1}.get(d, 0.5)


def compute_expected_alpha(
    source_proximity: float = 0.5,
    novelty: float = 0.5,
    bottleneck_relevance: float = 0.3,
    specificity: float = 0.5,
    surprise: float = 0.3,
    promotion: float = 0.0,
    repetition: float = 0.0,
    consensus_saturation: float = 0.0,
    performative_posting: float = 0.0,
) -> float:
    """Compute expected alpha score for a post.
    
    alpha = (source_proximity × novelty × bottleneck_relevance × specificity × surprise) /
            (promotion + repetition + consensus_saturation + performative_posting + 0.1)
    
    The 0.1 prevents division by zero for perfect posts.
    """
    numerator = source_proximity * novelty * bottleneck_relevance * specificity * surprise
    denominator = promotion + repetition + consensus_saturation + performative_posting + 0.1
    return round(clamp(numerator / denominator), 4)


def _text(item: NormalizedItem) -> str:
    return f"{item.title} {item.body or ''} {' '.join(map(str, item.metrics.get('topics', [])))}".lower()


# Claim classification keywords
_CLAIM_KEYWORDS = {
    "theory": ["bottleneck", "because", "the reason", "mechanism", "implies", "therefore", "causes"],
    "problem": ["fails", "broken", "trapped", "stuck", "limitation", "can't", "doesn't work", "struggle"],
    "observation": ["i found", "we observed", "experiment", "result", "data shows", "measured"],
    "prediction": ["will become", "going to", "next bottleneck", "future", "expect", "trend"],
    "evidence_for": ["confirms", "supports", "proves", "validates", "consistent with"],
    "evidence_against": ["contradicts", "refutes", "against", "but we found", "however"],
}


def classify_claim(text: str) -> str:
    """Classify a claim by type based on keywords."""
    text_lower = text.lower()
    scores = {}
    for kind, keywords in _CLAIM_KEYWORDS.items():
        scores[kind] = sum(1 for k in keywords if k in text_lower)
    if max(scores.values()) == 0:
        return "claim"
    return max(scores, key=scores.get)


def infer_domain(item: NormalizedItem) -> str:
    text = _text(item)
    if any(k in text for k in ("shopify", "commerce", "marketplace", "retail", "checkout", "ecommerce")):
        return "commerce"
    if any(k in text for k in ("ios", "iphone", "app store", "mobile app", "revenuecat")):
        return "ios"
    if any(k in text for k in ("seo", "search", "crawl", "indexnow", "serp")):
        return "seo"
    if any(k in text for k in ("mcp", "agent", "tool", "api", "sdk", "protocol")):
        return "agents"
    if any(k in text for k in ("ads", "meta", "tiktok", "creative", "acquisition")):
        return "distribution"
    if any(k in text for k in ("quantum", "qubit", "cryogenic", "photonics", "post-quantum", "q-day", "foundry", "wafer",
                               "trapped ion", "superconducting", "transmon", "qpu", "phonon", "dilution", "pq ", "pqc")):
        return "quantum"
    if any(k in text for k in ("robot", "embodied", "sim2real", "manipulation", "locomotion")):
        return "robotics"
    if any(k in text for k in ("world model", "spatial", "3d", "nerf", "gaussian")):
        return "world-models"
    if any(k in text for k in ("synbio", "synthetic biology", "cell", "ribosome", "gene", "crispr")):
        return "synbio"
    if any(k in text for k in ("neuromorphic", "spiking", "memristor", "analog compute")):
        return "neuromorphic"
    if any(k in text for k in ("hbm", "dram", "memory", "sram", "nand")):
        return "hardware"
    if any(k in text for k in ("bottleneck", "scarcity", "constraint", "limiting factor")):
        return "bottleneck"
    return "general"


def _make_object_key(item: NormalizedItem, kind: str, suffix: str = "") -> str:
    """Generate a stable dedup key for an object."""
    base = item.source_type.lower().replace(" ", "_")
    title_slug = item.title.lower().replace(" ", "_")[:64]
    return f"{kind}:{base}:{title_slug}{':' + suffix if suffix else ''}"


def _extract_entities(text: str) -> list[str]:
    """Extract entity mentions (companies, tickers, people) from text."""
    import re
    tickers = re.findall(r'\b([A-Z]{2,5})\b', text)
    return list(set(tickers))


def compile_artifact(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    """The semantic compiler: extracts typed objects and edges from an artifact.
    Replaces the old detect() function. Returns (objects, edges)."""
    fn = globals().get(f"compile_{item.source_type}")
    if callable(fn):
        result = fn(item, artifact_id)
        if result:
            return result
    return compile_generic(item, artifact_id)


def compile_trustmrr(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    m = item.metrics
    revenue = float(m.get("last30d_revenue_cents") or 0) / 100
    growth_raw = m.get("growth30d")
    growth = float(growth_raw or 0)
    growth_pct = growth * 100 if abs(growth) <= 2 else growth
    multiple = m.get("multiple")
    domain = "ios" if m.get("category") == "mobile-apps" else "commerce" if m.get("category") == "ecommerce" else "startups"

    objects: list[ObjectDraft] = []
    edges: list[EdgeDraft] = []

    company_key = f"entity:company:{item.title.lower().replace(' ', '_')}"

    if revenue >= 1_000 and growth_pct >= 10:
        objects.append(ObjectDraft(
            object_key=f"pick:{item.title.lower().replace(' ', '_')}",
            kind="pick",
            title=f"{item.title} — verified revenue acceleration",
            summary=f"Verified last-30-day revenue ${revenue:,.0f}, 30-day growth {growth_pct:.1f}%. Economic validation present.",
            confidence=0.9,
            domain=domain,
            tags=["verified-revenue", "breakout"],
        ))
        edges.append(EdgeDraft(
            source_key=f"entity:company:{item.title.lower().replace(' ', '_')}",
            target_key=f"pick:{item.title.lower().replace(' ', '_')}",
            relation="evidence_for",
            weight=0.9,
            evidence_artifact_id=artifact_id,
        ))

    if m.get("on_sale") and multiple is not None and float(multiple) <= 2.5:
        objects.append(ObjectDraft(
            object_key=f"idea:acquisition:{item.title.lower().replace(' ', '_')}",
            kind="idea",
            title=f"{item.title} — acquisition mispricing",
            summary=f"Listed at {float(multiple):.2f}x with ~${revenue:,.0f} MRR. Reveals validated niche.",
            confidence=0.86,
            domain="startups",
            tags=["acquisition", "validated-niche"],
        ))

    if not objects:
        objects.append(ObjectDraft(
            object_key=f"entity:company:{item.title.lower().replace(' ', '_')}",
            kind="entity",
            title=item.title,
            summary=f"Verified business: ~${revenue:,.0f} last-30-day revenue.",
            confidence=0.9,
            domain=domain,
        ))

    return objects, edges


def compile_glama(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    text = _text(item)
    commerce = any(x in text for x in ("commerce", "retail", "shop", "marketplace", "payment"))
    cats = [str(x) for x in (item.metrics.get("categories") or [])]

    objects = [ObjectDraft(
        object_key=f"entity:mcp:{item.title.lower().replace(' ', '_')}",
        kind="technology",
        title=f"MCP capability: {item.title}",
        summary=item.body or f"Discoverable MCP server from {item.author or 'an independent builder'}.",
        confidence=0.78,
        domain="commerce" if commerce else "agents",
        tags=["mcp", "primitive", *cats[:4]],
    )]
    edges: list[EdgeDraft] = []
    return objects, edges


def compile_github(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    stars = int(item.metrics.get("stars") or 0)
    topics = item.metrics.get("topics") or []

    objects = [ObjectDraft(
        object_key=f"entity:repo:{item.title.lower().replace(' ', '_')}",
        kind="technology",
        title=f"Repo: {item.title}",
        summary=f"{stars:,} stars. {item.body or ''}".strip(),
        confidence=0.78,
        domain=infer_domain(item),
        tags=["github", "open-source", *topics[:5]],
    )]
    edges: list[EdgeDraft] = []
    return objects, edges


def compile_hackernews(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    objects = [ObjectDraft(
        object_key=f"idea:launch:{item.title.lower().replace(' ', '_')[:48]}",
        kind="idea",
        title=item.title.replace("Show HN:", "Early launch:").strip(),
        summary=item.body or "Early builder launch surfaced on Hacker News.",
        confidence=0.62,
        domain=infer_domain(item),
        tags=["show-hn", "early"],
    )]
    edges: list[EdgeDraft] = []
    return objects, edges


def compile_storeleads(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    m = item.metrics
    delta = int(m.get("installs_30d") or 0)
    installs = int(m.get("installs") or 0)

    objects = [ObjectDraft(
        object_key=f"entity:shopify_app:{item.title.lower().replace(' ', '_')}",
        kind="entity",
        title=f"Shopify app: {item.title}",
        summary=f"{installs:,} installs, {delta:+,} net over 30 days.",
        confidence=0.88,
        domain="commerce",
        tags=["shopify", "app-adoption"],
    )]
    edges: list[EdgeDraft] = []
    return objects, edges


def compile_appfigures(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    revenue = float(item.metrics.get("revenue_30d") or 0)
    downloads = int(item.metrics.get("downloads_30d") or 0)

    objects = [ObjectDraft(
        object_key=f"entity:app:{item.title.lower().replace(' ', '_')}",
        kind="entity",
        title=f"App: {item.title}",
        summary=f"{downloads:,} downloads, ${revenue:,.0f} revenue (30d).",
        confidence=0.82,
        domain="ios",
        tags=["app-store", "revenue-estimate"],
    )]
    edges: list[EdgeDraft] = []
    return objects, edges


def compile_rss(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    objects = [ObjectDraft(
        object_key=f"idea:platform:{item.title.lower().replace(' ', '_')[:48]}",
        kind="claim",
        title=item.title,
        summary=(item.body or "")[:700],
        confidence=0.82,
        domain=infer_domain(item),
        tags=["rss", "primary-source"],
    )]
    edges: list[EdgeDraft] = []
    return objects, edges


SCARCITY_MAP: list[tuple[str, list[str], list[str]]] = [
    ("quantum fabrication", ["fab", "foundry", "manufacturing", "cryogenic cmos", "packaging"], ["GFS"]),
    ("wafer test", ["wafer", "cryogenic test", "probing", "yield", "4 kelvin", "millikelvin"], ["FORM"]),
    ("qubit control", ["control", "readout", "microwave", "rf ", "metrology", "benchmark"], ["KEYS"]),
    ("cryogenics", ["dilution refrigerator", "cryostat", "millikelvin", "bluefors"], ["OXIG"]),
    ("photonics", ["photonic", "laser", "optical interconnect", "pic "], ["COHR", "LITE"]),
    ("trapped ion", ["trapped ion", "ionq", "quantinuum"], ["IONQ", "QNT"]),
    ("superconducting", ["superconducting", "transmon"], ["RGTI"]),
    ("annealing", ["anneal", "d-wave", "dwave"], ["QBTS"]),
    ("pq migration", ["post-quantum", "pqc", "q-day", "nists", "ml-dsa", "ml-kem"], ["ETH"]),
    ("pq token", ["quantum-resistant ledger", "qrl", "qanplatform", "cellframe"], ["QRL", "QANX", "CELL"]),
]


def compile_x(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    """Compile an X post into objects and edges with scoring.
    
    Uses source_distance from watchlist, claim classification, and expected_alpha scoring.
    Only creates objects if alpha is above threshold.
    """
    text = _text(item)
    followers = int(item.metrics.get("author_followers") or 0)
    views = int(item.metrics.get("views") or 0)
    likes = int(item.metrics.get("likes") or 0)
    author_handle = item.metrics.get("author_handle", "")

    objects: list[ObjectDraft] = []
    edges: list[EdgeDraft] = []

    # Get source proximity from watchlist
    source_proximity = get_source_proximity(author_handle)

    # Classify the claim
    claim_type = classify_claim(item.title + " " + (item.body or ""))

    # Check for scarcity keywords
    implied: list[str] = []
    for _layer, keywords, tickers in SCARCITY_MAP:
        if any(k in text for k in keywords):
            implied.extend(t for t in tickers if t not in implied)

    # Compute scoring components
    # Novelty: penalize if text is very short or generic
    text_len = len(item.body or "")
    novelty = clamp(0.3 + min(text_len, 500) / 1000)
    
    # Bottleneck relevance: high if scarcity keywords, medium if claim/theory/problem
    bottleneck_relevance = 0.8 if implied else 0.5 if claim_type in ("theory", "problem") else 0.2
    
    # Specificity: check for numbers, mechanisms, specific names
    has_numbers = bool(re.search(r'\d+', text))
    has_mechanism = any(k in text for k in ["because", "mechanism", "caused by", "results in", "leads to", "gated by"])
    specificity = clamp(0.3 + (0.3 if has_numbers else 0) + (0.4 if has_mechanism else 0))
    
    # Surprise: inverse of how common this type of claim is
    surprise = 0.7 if claim_type in ("theory", "problem", "evidence_for", "evidence_against") else 0.3
    
    # Promotion: self-promotion signals
    promotion = 0.8 if any(k in text for k in ["follow me", "subscribe", "check out my", "join my"]) else 0.0
    
    # Repetition: check for common/generic phrases
    repetition = 0.7 if any(k in text for k in ["great thread", "hot take", "unpopular opinion", "change my mind"]) else 0.0
    
    # Consensus saturation: if everyone says this, it's saturated
    consensus_saturation = 0.5 if any(k in text for k in ["everyone knows", "obviously", "clearly", "as we all know"]) else 0.0
    
    # Performative posting: engagement bait
    performative_posting = 0.8 if any(k in text for k in ["like if", "rt if", "reply with", "quote tweet"]) else 0.0

    # Compute expected alpha
    expected_alpha = compute_expected_alpha(
        source_proximity=source_proximity,
        novelty=novelty,
        bottleneck_relevance=bottleneck_relevance,
        specificity=specificity,
        surprise=surprise,
        promotion=promotion,
        repetition=repetition,
        consensus_saturation=consensus_saturation,
        performative_posting=performative_posting,
    )

    # Score breakdown for metadata
    score_breakdown = {
        "source_proximity": source_proximity,
        "novelty": novelty,
        "bottleneck_relevance": bottleneck_relevance,
        "specificity": specificity,
        "surprise": surprise,
        "promotion": promotion,
        "repetition": repetition,
        "consensus_saturation": consensus_saturation,
        "performative_posting": performative_posting,
        "expected_alpha": expected_alpha,
    }

    # Skip low-alpha posts
    if expected_alpha < 0.15 and not implied:
        return [], []

    # Create person entity with source_distance info
    if author_handle:
        source_distance = get_source_distance(author_handle)
        person_key = f"entity:person:{author_handle.lower()}"
        objects.append(ObjectDraft(
            object_key=person_key,
            kind="person",
            title=author_handle,
            summary=f"X user, {followers:,} followers, source_distance={source_distance}",
            confidence=source_proximity,
            domain=infer_domain(item),
            tags=["x", "person", f"distance:{source_distance}"],
            metadata={"source_distance": source_distance, "followers": followers},
        ))

    # Handle scarcity tickers
    if implied:
        for ticker in implied:
            ticker_key = f"entity:ticker:{ticker}"
            objects.append(ObjectDraft(
                object_key=ticker_key,
                kind="company",
                title=ticker,
                summary=f"Mentioned in scarcity context: {(item.body or item.title or '')[:200]}",
                confidence=0.6,
                domain="quantum",
                tags=["scarcity-shock", ticker.lower()],
                metadata={"implied_tickers": implied, "author_handle": author_handle, "score": score_breakdown},
            ))
            objects.append(ObjectDraft(
                object_key="theory:ai-physical-bottleneck",
                kind="theory",
                title="AI Physical Bottleneck Migration",
                summary="As AI makes generation cheaper, physical validation, packaging and energy become progressively more important constraints.",
                confidence=0.7,
                domain="quantum",
                tags=["bottleneck", "thesis"],
            ))
            edges.append(EdgeDraft(
                source_key=ticker_key,
                target_key="theory:ai-physical-bottleneck",
                relation="evidence_for",
                weight=0.6,
                evidence_artifact_id=artifact_id,
            ))
        return objects, edges

    # Create the main object with classified claim type
    claim_key = f"{claim_type}:{item.title.lower().replace(' ', '_')[:48]}"
    objects.append(ObjectDraft(
        object_key=claim_key,
        kind=claim_type,
        title=item.title,
        summary=(item.body or "")[:700],
        confidence=clamp(expected_alpha + 0.3),  # boost confidence for high-alpha posts
        domain=infer_domain(item),
        tags=["x", claim_type],
        metadata={
            "viral": views >= 5000 and likes >= 100,
            "views": views,
            "likes": likes,
            "author_handle": author_handle,
            "score": score_breakdown,
        },
    ))

    return objects, edges


def compile_sec_edgar(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    from .insider_scoring import score_transaction

    m = item.metrics
    filing_type = m.get("filing_type", "")
    ticker = m.get("issuer_ticker", "")
    score_result = score_transaction(m)
    score = score_result["score"]
    tier = score_result["tier"]
    signal_type = score_result["signal_type"]
    is_frontier = score_result.get("is_frontier", False)

    objects: list[ObjectDraft] = []
    edges: list[EdgeDraft] = []

    owner = m.get("reporting_owner", "an insider")
    total_value = m.get("total_value", 0)

    # The insider is a person entity
    person_key = f"entity:person:{owner.lower().replace(' ', '_')}"
    objects.append(ObjectDraft(
        object_key=person_key,
        kind="person",
        title=owner,
        summary=f"Insider at {ticker}.",
        confidence=0.9,
        domain="insiders" if not is_frontier else "quantum",
        tags=["insider"],
    ))

    # The company
    company_key = f"entity:ticker:{ticker}"
    objects.append(ObjectDraft(
        object_key=company_key,
        kind="company",
        title=ticker,
        summary=f"SEC {filing_type} filing.",
        confidence=0.95,
        domain="insiders" if not is_frontier else "quantum",
        tags=["sec-filing", ticker.lower()],
    ))

    # The claim/decision
    if signal_type == "HIGH_SIGNAL_PURCHASE":
        claim_key = f"decision:insider_buy:{ticker}:{owner.lower().replace(' ', '_')}"
        objects.append(ObjectDraft(
            object_key=claim_key,
            kind="decision",
            title=f"{owner} bought ${total_value:,.0f} of {ticker}",
            summary=f"High-signal open-market purchase. Score {score:.1f}, tier {tier}.",
            confidence=0.9,
            domain="insiders" if not is_frontier else "quantum",
            tags=["insider-buy", "high-signal", ticker.lower()],
            metadata={"insider_score": score, "insider_tier": tier, **m},
        ))
        edges.append(EdgeDraft(source_key=person_key, target_key=company_key, relation="about", weight=0.9, evidence_artifact_id=artifact_id))
        edges.append(EdgeDraft(source_key=claim_key, target_key=company_key, relation="evidence_for", weight=0.85, evidence_artifact_id=artifact_id))
    else:
        claim_key = f"claim:insider:{ticker}:{owner.lower().replace(' ', '_')}"
        objects.append(ObjectDraft(
            object_key=claim_key,
            kind="claim",
            title=f"Insider activity: {owner} at {ticker}",
            summary=f"Score {score:.1f}, tier {tier}.",
            confidence=0.8,
            domain="insiders" if not is_frontier else "quantum",
            tags=["insider", ticker.lower()],
            metadata={"insider_score": score, "insider_tier": tier, **m},
        ))
        edges.append(EdgeDraft(source_key=person_key, target_key=company_key, relation="about", weight=0.8, evidence_artifact_id=artifact_id))

    return objects, edges


def compile_openinsider(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    from .insider_scoring import score_transaction

    m = item.metrics
    score_result = score_transaction(m)
    ticker = m.get("issuer_ticker", "")
    owner = m.get("reporting_owner", "an insider")

    objects: list[ObjectDraft] = []
    edges: list[EdgeDraft] = []

    person_key = f"entity:person:{owner.lower().replace(' ', '_')}"
    company_key = f"entity:ticker:{ticker}"

    objects.append(ObjectDraft(
        object_key=person_key,
        kind="person",
        title=owner,
        summary=f"Insider at {ticker} (OpenInsider).",
        confidence=0.88,
        domain="insiders",
        tags=["openinsider"],
    ))
    objects.append(ObjectDraft(
        object_key=company_key,
        kind="company",
        title=ticker,
        summary=f"OpenInsider data.",
        confidence=0.88,
        domain="insiders",
        tags=["openinsider", ticker.lower()],
    ))
    edges.append(EdgeDraft(source_key=person_key, target_key=company_key, relation="about", weight=0.8, evidence_artifact_id=artifact_id))

    return objects, edges


def compile_generic(item: NormalizedItem, artifact_id: int) -> tuple[list[ObjectDraft], list[EdgeDraft]]:
    objects = [ObjectDraft(
        object_key=_make_object_key(item, "claim"),
        kind="claim",
        title=item.title,
        summary=(item.body or "")[:700],
        confidence=0.5,
        domain=infer_domain(item),
        tags=[item.source_type],
    )]
    edges: list[EdgeDraft] = []
    return objects, edges


def compile_many(items: Iterable[NormalizedItem]) -> list[tuple[NormalizedItem, ObjectDraft]]:
    return [(item, obj) for item in items for obj, _ in [compile_artifact(item, 0)]]
