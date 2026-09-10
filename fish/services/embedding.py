"""Embedding service for semantic search in Feedify 2.0.

Uses OpenAI-compatible embedding API. Falls back to a simple TF-IDF approach
when no API key is available.

For SQLite: stores embeddings as JSON, computes cosine similarity in Python.
For Postgres: would use pgvector extension.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Any

import httpx

from fish.settings import get_settings


def _simple_embed(text: str, dim: int = 128) -> list[float]:
    """Deterministic TF-IDF-like embedding when no API is available.
    Not as good as real embeddings, but enables semantic search immediately."""
    words = text.lower().split()
    if not words:
        return [0.0] * dim

    # Use word positions to create a fixed-dim vector
    vec = [0.0] * dim
    for i, word in enumerate(words):
        h = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
        idx = h % dim
        # Position-weighted: earlier words get slightly more weight
        weight = 1.0 / (1.0 + i * 0.1)
        vec[idx] += weight

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


async def get_embedding(text: str) -> list[float]:
    """Get an embedding vector for text. Uses API if available, else simple hash embedding."""
    settings = get_settings()

    if settings.llm_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(
                    f"{settings.llm_base_url.rstrip('/')}/embeddings",
                    headers={"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"},
                    json={"model": "text-embedding-3-small", "input": text[:8000]},
                )
                if res.status_code == 200:
                    data = res.json()
                    return data["data"][0]["embedding"]
        except Exception:
            pass

    return _simple_embed(text)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        # Truncate to shorter
        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (norm_a * norm_b)


def compute_embedding_text(title: str, summary: str, domain: str, kind: str) -> str:
    """Compute the text to embed for an object."""
    return f"{kind}: {title}. {summary}. Domain: {domain}"
