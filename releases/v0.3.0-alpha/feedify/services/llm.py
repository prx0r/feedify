from __future__ import annotations

import json
from typing import Any

import httpx

from feedify.settings import get_settings


async def enrich_signal(payload: dict[str, Any]) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.llm_api_key:
        return None
    system = (
        "You are Feedify's signal analyst. Return ONLY valid JSON with keys: summary, why_it_matters, "
        "novelty, actionability, source_proximity, confidence, evidence_strength, tags. Scores are 0..1. "
        "Prefer concrete newly enabled capabilities and economically grounded evidence; punish generic commentary."
    )
    async with httpx.AsyncClient(timeout=45) as client:
        res = await client.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"},
            json={
                "model": settings.llm_model,
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)[:16000]},
                ],
            },
        )
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
