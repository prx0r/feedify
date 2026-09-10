"""LLM-powered semantic compiler for Feedify 2.0.

Extracts typed Objects and Edges from artifacts using LLM intelligence.
Classifies claims by type (theory/observation/problem/evidence_for etc.).
Extracts relationships between objects.
Scores posts for expected alpha before ingestion.
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from fish.schemas import NormalizedItem, ObjectDraft, EdgeDraft
from fish.settings import get_settings


SYSTEM_PROMPT = """You are Feedify's semantic compiler. You receive raw information artifacts
(tweets, filings, papers, posts, news) and extract structured knowledge.

CRITICAL: Classify each claim by type. Not everything is a "claim".

Return ONLY valid JSON with this exact shape:
{
  "objects": [
    {
      "object_key": "kind:slug (stable dedup key, lowercase, underscores, max 64 chars)",
      "kind": "entity|person|company|technology|idea|claim|theory|problem|question|decision|prediction|pick|observation|evidence_for|evidence_against",
      "title": "concise title — what was actually said/discovered",
      "summary": "2-3 sentence summary of the actual intellectual content, not the raw text",
      "confidence": 0.0-1.0,
      "domain": "ai-research|robotics|synbio|hardware|materials|power|neuroscience|cognition|world-models|embodied|ai4science|self-improving|stocks|quantum|general",
      "tags": ["relevant", "tags"]
    }
  ],
  "edges": [
    {
      "source_key": "object_key of source",
      "target_key": "object_key of target",
      "relation": "supports|contradicts|supersedes|causes|depends_on|evidence_for|evidence_against|mentions|related_to|about",
      "weight": 0.0-1.0
    }
  ],
  "score": {
    "source_proximity": 0.0-1.0,
    "novelty": 0.0-1.0,
    "bottleneck_relevance": 0.0-1.0,
    "specificity": 0.0-1.0,
    "surprise": 0.0-1.0,
    "promotion": 0.0-1.0,
    "repetition": 0.0-1.0,
    "consensus_saturation": 0.0-1.0,
    "performative_posting": 0.0-1.0,
    "expected_alpha": 0.0-1.0
  }
}

CLASSIFICATION RULES:
- theory: causal claim about how something works ("the bottleneck moved from X to Y")
- observation: empirical report of what was seen ("my experiment showed X")
- problem: something broken or suboptimal ("models keep getting trapped in local search")
- evidence_for: data supporting an existing theory ("3 independent sources confirm X")
- evidence_against: data contradicting a theory ("we tested X and found Y instead")
- prediction: claim about what will happen ("this will become the next bottleneck")
- decision: a choice made ("we switched from X to Y")
- pick: specific company/tool/person recommended
- entity: company, person, organization
- technology: tool, framework, method
- question: open question worth tracking

SCORING RULES:
- source_proximity: 0=influencer, 0.3=analyst, 0.5=journalist, 0.7=specialist, 0.9=experimenter
- novelty: how new is this claim vs common knowledge
- bottleneck_relevance: does this relate to a physical/economic bottleneck
- specificity: does it include specific numbers, mechanisms, names
- surprise: how unexpected is this finding
- promotion: 0=none, 1=heavy self-promotion
- repetition: 0=novel, 1=commonly repeated
- consensus_saturation: 0=controversial, 1=universally accepted
- performative_posting: 0=genuine, 1=engagement bait
- expected_alpha: computed as (source_proximity × novelty × bottleneck_relevance × specificity × surprise) / (promotion + repetition + consensus_saturation + performative_posting + 0.1)

RELATIONSHIP RULES:
- supports: agrees with or reinforces another object
- contradicts: disagrees with or challenges another object
- supersedes: replaces or updates an older claim
- causes: one thing leads to another
- evidence_for: data supporting a theory/claim
- evidence_against: data contradicting a theory/claim
- mentions: references a person/company/concept
- about: the post is about this entity/concept
- related_to: general connection

Keep summaries under 200 words. Return empty arrays if nothing meaningful is found.
If the post is just casual conversation, reply, or engagement bait, return score.expected_alpha < 0.2."""


async def llm_compile(artifact: NormalizedItem) -> tuple[list[ObjectDraft], list[EdgeDraft], dict[str, float]]:
    """Use LLM to extract objects, edges, and alpha score from an artifact.
    Returns (objects, edges, score_breakdown)."""
    settings = get_settings()
    if not settings.llm_api_key:
        return [], [], {}

    content = f"SOURCE: {artifact.source_type}\n"
    if artifact.author:
        content += f"AUTHOR: {artifact.author}\n"
    content += f"TITLE: {artifact.title}\n"
    if artifact.url:
        content += f"URL: {artifact.url}\n"
    if artifact.body:
        content += f"BODY: {artifact.body[:3000]}\n"
    if artifact.metrics:
        content += f"METRICS: {json.dumps(artifact.metrics, default=str)[:1000]}\n"

    try:
        is_muse = "muse" in settings.llm_model.lower()

        async with httpx.AsyncClient(timeout=60) as client:
            if is_muse:
                # Muse Spark needs the Responses API
                res = await client.post(
                    f"{settings.llm_base_url.rstrip('/')}/responses",
                    headers={
                        "Authorization": f"Bearer {settings.llm_api_key}",
                        "Content-Type": "application/json",
                        "x-opencode-session": "feedify-compiler",
                    },
                    json={
                        "model": settings.llm_model,
                        "input": f"{SYSTEM_PROMPT}\n\n{content[:14000]}",
                    },
                )
                res.raise_for_status()
                data = res.json()
                raw = ""
                for item in data.get("output", []):
                    if item.get("type") == "message":
                        for c in item.get("content", []):
                            raw += c.get("text", "")
            else:
                # Standard Chat Completions API
                res = await client.post(
                    f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.llm_api_key}",
                        "Content-Type": "application/json",
                        "x-opencode-session": "feedify-compiler",
                    },
                    json={
                        "model": settings.llm_model,
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": content[:16000]},
                        ],
                    },
                )
                res.raise_for_status()
                data = res.json()
                raw = data["choices"][0]["message"]["content"]
            data = json.loads(raw)

            objects = []
            for obj in data.get("objects", []):
                objects.append(ObjectDraft(
                    object_key=obj.get("object_key", f"unknown:{artifact.source_type}"),
                    kind=obj.get("kind", "claim"),
                    title=obj.get("title", artifact.title),
                    summary=obj.get("summary", artifact.body or artifact.title),
                    confidence=float(obj.get("confidence", 0.5)),
                    domain=obj.get("domain", "general"),
                    tags=obj.get("tags", []),
                    metadata={"llm_compiled": True, "source_type": artifact.source_type},
                ))

            edges = []
            for edge in data.get("edges", []):
                edges.append(EdgeDraft(
                    source_key=edge.get("source_key", ""),
                    target_key=edge.get("target_key", ""),
                    relation=edge.get("relation", "related_to"),
                    weight=float(edge.get("weight", 0.5)),
                ))

            score = data.get("score", {})

            return objects, edges, score

    except Exception:
        return [], [], {}


def _make_stable_key(item: NormalizedItem, kind: str) -> str:
    """Generate a stable dedup key for an artifact."""
    title_slug = re.sub(r'[^a-z0-9]+', '_', item.title.lower())[:48].strip('_')
    return f"{kind}:{item.source_type}:{title_slug}"
