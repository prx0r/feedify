"""AI summarization service using mimov2.5."""
from __future__ import annotations

import json
from typing import Any

import httpx

from fish.settings import get_settings


async def _call_llm(prompt: str, api_key: str = "", max_tokens: int = 1500) -> str:
    """Call LLM API with fallback."""
    settings = get_settings()
    
    # Try OpenRouter first (existing config)
    if settings.llm_api_key:
        url = f"{settings.llm_base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
        model = settings.llm_model or "deepseek/deepseek-chat-v3-0324"
    # Try the user's key with OpenRouter
    elif api_key and api_key.startswith("sk-"):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        model = "deepseek/deepseek-chat-v3-0324"
    else:
        return "AI analysis not available — no LLM API key configured."

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "x-opencode-session": "feedify-insiders",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.3,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return f"AI temporarily unavailable (HTTP {resp.status_code}). Using rule-based scoring."
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI error: {e}. Using rule-based scoring."


async def summarize_insiders(signals: list[dict[str, Any]], api_key: str = "") -> str:
    """Summarize insider signals into actionable alpha."""
    if not signals:
        return "No insider signals to analyze."

    # Build context from signals
    context_lines = []
    for s in signals[:30]:  # Top 30 signals
        ticker = s.get("ticker", "?")
        owner = s.get("owner", "?")
        score = s.get("score", 0)
        tier = s.get("tier", "?")
        txn = s.get("txn_label", "?")
        value = s.get("total_value", 0)
        verified = "✓ VERIFIED" if s.get("is_verified") else "🔍 X DISCOVERY"
        date = s.get("created_at", "")[:10]

        line = f"[{date}] {ticker} — {owner} — ${abs(value):,.0f} {txn} (Score: {score}/100, Tier: {tier}, {verified})"
        context_lines.append(line)

    signals_text = "\n".join(context_lines)

    prompt = f"""You are an insider trading intelligence analyst. Analyze these insider signals and tell me:

1. What are the TOP 3 highest-alpha signals right now? Why?
2. Any cluster buying patterns (multiple insiders buying the same stock)?
3. Any FRONTIER stock (AI, chips, quantum, power) insider activity?
4. What should I pay attention to vs ignore?
5. Any unusual patterns?

SIGNALS:
{signals_text}

Be direct. No hedging. Tell me what matters and why."""

    return await _call_llm(prompt, api_key)


async def chat_with_insiders(
    message: str,
    signals: list[dict[str, Any]],
    api_key: str = "",
    history: list[dict[str, str]] | None = None,
) -> str:
    """Chat about insider signals with AI context."""
    # Build signal context
    context_lines = []
    for s in signals[:20]:
        ticker = s.get("ticker", "?")
        owner = s.get("owner", "?")
        score = s.get("score", 0)
        txn = s.get("txn_label", "?")
        value = s.get("total_value", 0)
        verified = "✓" if s.get("is_verified") else "🔍"
        date = s.get("created_at", "")[:10]
        interp = s.get("interpretation", "")

        context_lines.append(
            f"{verified} [{date}] {ticker} — {owner} — ${abs(value):,.0f} {txn} "
            f"(Score: {score}/100) | {interp}"
        )

    signals_text = "\n".join(context_lines)

    system = f"""You are an insider trading intelligence analyst for Feedify. You have access to real insider signals from SEC filings and X/Twitter discovery.

CURRENT SIGNALS:
{signals_text}

RULES:
- Be direct and opinionated
- Reference specific signals by ticker/owner
- Distinguish verified SEC filings (✓) from X discovery (🔍)
- Focus on ACTIONABLE alpha, not noise
- If asked about a specific ticker, search the signals for it
- If asked to compare sources, use the data"""

    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-6:])  # Last 3 exchanges
    messages.append({"role": "user", "content": message})

    settings = get_settings()
    url = f"{settings.llm_base_url}/chat/completions"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key or api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model or "deepseek/deepseek-chat-v3-0324",
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.4,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return f"AI temporarily unavailable (HTTP {resp.status_code}). Try again later."
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI error: {e}"
