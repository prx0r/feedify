"""ChatGPT Conversation Importer for Feedify 2.0.

Imports ChatGPT conversations and compiles them into the knowledge graph.
Extracts: ideas, theories, recurring problems, decisions, picks, predictions,
unresolved questions, and projects.

An uploaded conversation shouldn't become 50,000 chat messages in a searchable
database. It should compile into your personal graph.
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from feedify.models import Object, Edge
from feedify.schemas import ObjectDraft, EdgeDraft
from feedify.settings import get_settings


EXTRACTION_SYSTEM = """You are Feedify's conversation compiler. You receive a ChatGPT conversation
and extract structured knowledge objects.

Return ONLY valid JSON with this shape:
{
  "objects": [
    {
      "object_key": "kind:slug (stable, lowercase, underscores)",
      "kind": "idea|theory|problem|decision|prediction|pick|question|project|person|entity|concept",
      "title": "concise title",
      "summary": "2-3 sentence summary",
      "confidence": 0.0-1.0,
      "domain": "general|...",
      "tags": ["relevant", "tags"]
    }
  ],
  "edges": [
    {
      "source_key": "object_key of source",
      "target_key": "object_key of target",
      "relation": "supports|contradicts|supersedes|causes|depends_on|related_to|about",
      "weight": 0.0-1.0
    }
  ]
}

Rules:
- Extract RECURRING problems (mentioned 3+ times)
- Extract DECISIONS (things the user chose or concluded)
- Extract PICKS (specific companies, tools, people recommended)
- Extract THEORIES (causal claims, not just observations)
- Extract OPEN QUESTIONS (things left unresolved)
- Extract PROJECTS (things being built or planned)
- Connect related objects with edges
- object_key must be stable across imports
- Focus on ACTIONABLE knowledge, not conversation filler
- Keep summaries under 150 words"""


async def import_conversation(
    session: Session,
    messages: list[dict[str, str]] | None = None,
    text: str | None = None,
    title: str = "Imported conversation",
) -> tuple[int, int]:
    """Import a ChatGPT conversation into the knowledge graph.
    Returns (objects_created, edges_created)."""

    if not messages and text:
        # Parse text into messages
        messages = _parse_text_conversation(text)

    if not messages:
        return 0, 0

    # Truncate to fit context window
    conversation_text = "\n".join(
        f"{m.get('role', 'unknown').upper()}: {m.get('content', '')[:2000]}"
        for m in messages[:100]
    )

    settings = get_settings()
    if not settings.llm_api_key:
        # Fallback: create a single summary object
        return _import_fallback(session, conversation_text, title)

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            res = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"},
                json={
                    "model": settings.llm_model,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": EXTRACTION_SYSTEM},
                        {"role": "user", "content": f"CONVERSATION: {title}\n\n{conversation_text[:14000]}"},
                    ],
                },
            )
            res.raise_for_status()
            raw = res.json()["choices"][0]["message"]["content"]
            data = json.loads(raw)

            objects_created = 0
            edges_created = 0

            for obj_data in data.get("objects", []):
                key = obj_data.get("object_key", "")
                if not key:
                    continue

                existing = session.scalar(
                    select(Object).where(Object.object_key == key, Object.version == 1)
                )
                if existing:
                    existing.title = obj_data.get("title", existing.title)
                    existing.summary = obj_data.get("summary", existing.summary)
                    existing.confidence = float(obj_data.get("confidence", existing.confidence))
                    existing.domain = obj_data.get("domain", existing.domain)
                    existing.metadata_json = {
                        **(existing.metadata_json or {}),
                        "source": "chatgpt_import",
                        "conversation_title": title,
                    }
                else:
                    session.add(Object(
                        object_key=key,
                        kind=obj_data.get("kind", "idea"),
                        title=obj_data.get("title", ""),
                        summary=obj_data.get("summary", ""),
                        confidence=float(obj_data.get("confidence", 0.5)),
                        domain=obj_data.get("domain", "general"),
                        metadata_json={
                            "tags": obj_data.get("tags", []),
                            "source": "chatgpt_import",
                            "conversation_title": title,
                        },
                    ))
                    objects_created += 1

            for edge_data in data.get("edges", []):
                source = session.scalar(
                    select(Object).where(Object.object_key == edge_data.get("source_key", ""), Object.version == 1)
                )
                target = session.scalar(
                    select(Object).where(Object.object_key == edge_data.get("target_key", ""), Object.version == 1)
                )
                if not source or not target:
                    continue

                existing_edge = session.scalar(
                    select(Edge).where(
                        Edge.source_id == source.id,
                        Edge.target_id == target.id,
                        Edge.relation == edge_data.get("relation", "related_to"),
                    )
                )
                if not existing_edge:
                    session.add(Edge(
                        source_id=source.id,
                        target_id=target.id,
                        relation=edge_data.get("relation", "related_to"),
                        weight=float(edge_data.get("weight", 0.5)),
                        metadata_json={"source": "chatgpt_import"},
                    ))
                    edges_created += 1

            return objects_created, edges_created

    except Exception:
        return _import_fallback(session, conversation_text, title)


def _parse_text_conversation(text: str) -> list[dict[str, str]]:
    """Parse a plain text conversation into messages."""
    messages = []
    current_role = None
    current_content = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if re.match(r'^(Human|User|Assistant|AI|You|Me):', line, re.IGNORECASE):
            if current_role and current_content:
                messages.append({"role": current_role, "content": "\n".join(current_content)})
            match = re.match(r'^(Human|User|Assistant|AI|You|Me):', line, re.IGNORECASE)
            role = match.group(1).lower()
            if role in ("human", "user", "me"):
                current_role = "user"
            else:
                current_role = "assistant"
            current_content = [line[match.end():].strip()]
        else:
            current_content.append(line)

    if current_role and current_content:
        messages.append({"role": current_role, "content": "\n".join(current_content)})

    return messages


def _import_fallback(session: Session, text: str, title: str) -> tuple[int, int]:
    """Fallback import when LLM is unavailable. Creates a single summary object."""
    slug = re.sub(r'[^a-z0-9]+', '_', title.lower())[:48].strip('_')

    # Check if already imported
    key = f"conversation:{slug}"
    existing = session.scalar(select(Object).where(Object.object_key == key, Object.version == 1))
    if existing:
        return 0, 0

    session.add(Object(
        object_key=key,
        kind="concept",
        title=title,
        summary=text[:500],
        confidence=0.4,
        domain="general",
        metadata_json={
            "source": "chatgpt_import",
            "fallback": True,
            "full_text": text[:5000],
        },
    ))
    return 1, 0
