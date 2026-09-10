"""Thesis synthesis engine — produces and updates theses from data.

The thesis is:
1. Synthesized from all data
2. Stored append-only
3. Updated when new data arrives
4. Continuously creates new theses
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fish.services.minimal_graph import MinimalGraph


# Thesis storage
THESIS_DIR = Path(__file__).parent.parent.parent / "data" / "theses"


def ensure_thesis_dir():
    THESIS_DIR.mkdir(parents=True, exist_ok=True)


def load_theses() -> list[dict[str, Any]]:
    """Load all theses from storage."""
    ensure_thesis_dir()
    theses = []
    for f in sorted(THESIS_DIR.glob("*.json")):
        try:
            theses.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return theses


def save_thesis(thesis: dict[str, Any]) -> None:
    """Save a thesis to storage."""
    ensure_thesis_dir()
    thesis_id = thesis.get("id", datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    thesis["id"] = thesis_id
    path = THESIS_DIR / f"{thesis_id}.json"
    path.write_text(json.dumps(thesis, indent=2))


def append_to_thesis(thesis_id: str, new_evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """Append new evidence to an existing thesis."""
    path = THESIS_DIR / f"{thesis_id}.json"
    if not path.exists():
        raise ValueError(f"Thesis {thesis_id} not found")
    
    thesis = json.loads(path.read_text())
    thesis["evidence"].extend(new_evidence)
    thesis["last_updated"] = datetime.now(timezone.utc).isoformat()
    thesis["evidence_count"] = len(thesis["evidence"])
    path.write_text(json.dumps(thesis, indent=2))
    return thesis


def get_thesis_context() -> str:
    """Get all theses as context for LLM."""
    theses = load_theses()
    if not theses:
        return "No theses yet."
    
    lines = ["## EXISTING THESES"]
    for t in theses:
        lines.append(f"\n### {t.get('title', 'Untitled')} (ID: {t.get('id', '?')})")
        lines.append(f"Created: {t.get('created_at', '?')}")
        lines.append(f"Last updated: {t.get('last_updated', '?')}")
        lines.append(f"Evidence count: {t.get('evidence_count', 0)}")
        lines.append(f"\n{t.get('statement', '')}")
        if t.get("implications"):
            lines.append(f"\nImplications: {t['implications']}")
        if t.get("falsification"):
            lines.append(f"\nFalsification: {t['falsification']}")
    
    return "\n".join(lines)


def build_thesis_prompt(graph: MinimalGraph, existing_theses: list[dict[str, Any]], recent_evidence: list[dict[str, Any]]) -> str:
    """Build a prompt for thesis synthesis."""
    
    # Build graph context
    graph_context = graph.to_llm_context()
    
    # Build evidence context
    evidence_lines = []
    for e in recent_evidence[:20]:
        evidence_lines.append(f"- [{e.get('source', '?')}] {e.get('title', '')[:80]}")
    evidence_context = "\n".join(evidence_lines) if evidence_lines else "No recent evidence."
    
    # Build existing theses context
    theses_context = get_thesis_context() if existing_theses else "No existing theses."
    
    prompt = f"""You are a technology intelligence analyst synthesizing theses from raw data.

EXISTING THESES:
{theses_context}

GRAPH DATA:
{graph_context}

RECENT EVIDENCE:
{evidence_context}

TASK:
1. If an existing thesis is strengthened or contradicted by new evidence, UPDATE it.
2. If a genuinely new pattern emerges that doesn't fit existing theses, CREATE a new thesis.
3. Each thesis must be:
   - A clear, falsifiable claim about technology direction
   - Supported by specific evidence (people, companies, signals)
   - Have explicit implications for the acceleration thesis
   - Have a falsification criterion

OUTPUT FORMAT (JSON):
{{
  "action": "update" or "create" or "none",
  "thesis_id": "existing-id or null for new",
  "title": "short title",
  "statement": "the thesis in 1-3 sentences",
  "implications": "what this means for the acceleration thesis",
  "falsification": "what would prove this wrong",
  "evidence_ids": ["list of supporting evidence"],
  "confidence": 0.0-1.0,
  "update_summary": "what changed if updating existing"
}}

If no update or new thesis is warranted, return:
{{"action": "none"}}

Be rigorous. Only create/update theses when there's genuine new signal."""

    return prompt


def synthesize_thesis(graph: MinimalGraph, recent_evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Synthesize a thesis from graph and evidence using LLM."""
    from fish.settings import get_settings
    
    existing_theses = load_theses()
    prompt = build_thesis_prompt(graph, existing_theses, recent_evidence)
    
    settings = get_settings()
    
    # Use OpenCode Go endpoint
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    api_key = settings.llm_api_key or "sk-A5QHR5MRtUNec7BWqiRsZ0GAYck0CRT2Movsk7Q6U3UwcV77Y6G3TMXOhhyKh855"
    model = "mimo-v2.5"
    
    try:
        import httpx
        import asyncio
        
        async def call():
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "x-opencode-session": "feedify-thesis",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2000,
                        "temperature": 0.3,
                    },
                    timeout=60,
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        
        result = asyncio.run(call())
        if not result:
            return None
        
        # Parse JSON from response
        import re
        # Try to find JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        # Try to find JSON object
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        # Try to find any JSON object
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
    except Exception as e:
        print(f"Thesis synthesis error: {e}")
    
    return None
