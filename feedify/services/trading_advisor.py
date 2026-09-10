"""Trading Advisor — LLM reasons over knowledge graph for trading advice.

The key: the LLM answers from the graph, not its training data.
Graph is source of truth. LLM is reasoning engine.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from feedify.settings import get_settings


TRADING_THEORY = """
TRADING THEORY REFERENCE:

SUPPORT/RESISTANCE:
- Support: price level where buying interest emerges (previous lows, consolidation zones)
- Resistance: price level where selling pressure emerges (previous highs, breakouts)
- Breakout: price closes above resistance on volume = bullish
- Breakdown: price closes below support on volume = bearish

VOLUME ANALYSIS:
- High volume on up days = accumulation (bullish)
- High volume on down days = distribution (bearish)
- Low volume pullback = healthy consolidation
- Volume spike after base = breakout confirmation

RISK MANAGEMENT:
- Position sizing: risk no more than 1-2% of portfolio per trade
- Stop loss: place below key support level
- Risk/reward: minimum 1:2 (risk £1 to make £2)
- Trailing stop: move stop up as price rises to lock gains
- Scale in: don't buy full position at once, scale in on pullbacks

PATTERN RECOGNITION:
- Cup and handle: bullish continuation pattern
- Head and shoulders: bearish reversal pattern
- Double bottom: bullish reversal
- Ascending triangle: bullish continuation
- Descending triangle: bearish continuation

MOVING AVERAGES:
- Price above 20-day MA = short-term uptrend
- Price above 50-day MA = medium-term uptrend
- Price above 200-day MA = long-term uptrend
- 20-day crossing above 50-day = golden cross (bullish)
- 20-day crossing below 50-day = death cross (bearish)

RELATIVE STRENGTH:
- RSI > 70 = overbought (potential sell)
- RSI < 30 = oversold (potential buy)
- RSI 40-60 = neutral

MONEY FLOW:
- On-balance volume rising = accumulation
- On-balance volume falling = distribution
- Chaikin money flow > 0 = buying pressure
"""


def build_trading_context(
    stock: dict[str, Any],
    graph_context: str,
    latest_report: dict[str, Any] | None,
    chat_memory: list[dict[str, Any]],
    user_preferences: dict[str, Any] | None = None,
) -> str:
    """Build the full context for the trading advisor."""
    context = f"""You are a professional trading advisor. You reason over a knowledge graph and stock data to give investment and trading advice.

CORE RULES:
1. Every claim must be backed by graph data or trading theory
2. Never give generic advice — always reference specific data
3. Always mention risk management (stop loss, position sizing)
4. If the graph shows contradictions, say so
5. If you don't have enough data, say so

{TRADING_THEORY}

CURRENT STOCK:
{json.dumps(stock, indent=2)}

KNOWLEDGE GRAPH (relevant objects):
{graph_context[:3000]}

LATEST REPORT:
{json.dumps(latest_report, indent=2) if latest_report else "No report yet"}

RECENT CHAT:
"""
    for m in chat_memory[:5]:
        context += f"User: {m.get('message', '')}\nAssistant: {m.get('response', '')[:200]}\n"

    if user_preferences:
        context += f"\nUSER PREFERENCES:\n{json.dumps(user_preferences, indent=2)}\n"

    return context


async def get_trading_response(
    message: str,
    stock: dict[str, Any],
    graph_context: str,
    latest_report: dict[str, Any] | None,
    chat_memory: list[dict[str, Any]],
) -> str:
    """Get trading advice from the agent."""
    settings = get_settings()
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    api_key = settings.llm_api_key or ""

    context = build_trading_context(stock, graph_context, latest_report, chat_memory)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "x-opencode-session": "feedify-trading-advisor",
                },
                json={
                    "model": "mimo-v2.5",
                    "messages": [
                        {"role": "system", "content": context},
                        {"role": "user", "content": message},
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return "AI temporarily unavailable."
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI error: {e}"


def generate_daily_brief(
    stock: dict[str, Any],
    graph_context: str,
    latest_report: dict[str, Any] | None,
) -> str:
    """Generate a bitesized daily brief for a stock."""
    ticker = stock.get("ticker", "?")
    name = stock.get("name", "?")
    price = stock.get("current_price", "?")
    thesis = stock.get("thesis", "")[:100]
    entry = stock.get("entry_price", "?")
    stop = stock.get("stop_loss", "?")
    target = stock.get("target_price", "?")

    brief = f"# {ticker} Daily — {datetime.now().strftime('%Y-%m-%d')}\n\n"
    brief += f"**{name}** | Price: {price}\n"
    brief += f"Entry: {entry} | Stop: {stop} | Target: {target}\n"
    brief += f"Thesis: {thesis}\n\n"

    if latest_report:
        brief += f"**Action**: {latest_report.get('action', 'HOLD')}\n"
        brief += f"**Summary**: {latest_report.get('summary', '')[:200]}\n"

    return brief
