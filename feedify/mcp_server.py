"""Feedify MCP Server — Model Context Protocol for Feedify intelligence.

Allows AI assistants to query Feedify data directly.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

FEEDIFY_BASE = "https://feedify.egoic.ai"


async def call_tool(tool: str, args: dict[str, Any]) -> Any:
    """Call a Feedify MCP tool."""
    async with httpx.AsyncClient() as client:
        if tool == "feedify_health":
            r = await client.get(f"{FEEDIFY_BASE}/api/health", timeout=10)
            return r.json()

        elif tool == "feedify_signals":
            limit = args.get("limit", 20)
            domain = args.get("domain")
            url = f"{FEEDIFY_BASE}/api/signals?limit={limit}"
            if domain:
                url += f"&domain={domain}"
            r = await client.get(url, timeout=10)
            return r.json()

        elif tool == "feedify_insiders":
            limit = args.get("limit", 20)
            r = await client.get(f"{FEEDIFY_BASE}/api/insiders?limit={limit}", timeout=10)
            return r.json()

        elif tool == "feedify_frontier":
            limit = args.get("limit", 20)
            signal_type = args.get("signal_type")
            lab = args.get("lab")
            url = f"{FEEDIFY_BASE}/api/frontier?limit={limit}"
            if signal_type:
                url += f"&signal_type={signal_type}"
            if lab:
                url += f"&lab={lab}"
            r = await client.get(url, timeout=10)
            return r.json()

        elif tool == "feedify_graph":
            r = await client.get(f"{FEEDIFY_BASE}/api/frontier/graph", timeout=15)
            return r.json()

        elif tool == "feedify_chat":
            message = args.get("message", "")
            context = args.get("context", "general")
            async with client.stream(
                "POST",
                f"{FEEDIFY_BASE}/api/chat",
                json={"message": message, "context": context},
                timeout=60,
            ) as r:
                return await r.aread()

        elif tool == "feedify_feeds":
            r = await client.get(f"{FEEDIFY_BASE}/api/feeds", timeout=10)
            return r.json()

        elif tool == "feedify_sources":
            r = await client.get(f"{FEEDIFY_BASE}/api/sources", timeout=10)
            return r.json()

        else:
            return {"error": f"Unknown tool: {tool}"}


# Tool definitions for MCP
TOOLS = [
    {
        "name": "feedify_health",
        "description": "Get Feedify system health status",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "feedify_signals",
        "description": "List recent signals from Feedify",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of signals to return (default 20)"},
                "domain": {"type": "string", "description": "Filter by domain (quantum, agents, insiders, etc.)"},
            },
        },
    },
    {
        "name": "feedify_insiders",
        "description": "List insider trading signals (SEC verified + X discovery)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of signals to return (default 20)"},
            },
        },
    },
    {
        "name": "feedify_frontier",
        "description": "List frontier quantum × AGI signals",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of signals to return (default 20)"},
                "signal_type": {"type": "string", "description": "Filter by type (CONVERGENCE, AGI_LEAD, QUANTUM_LEAD, etc.)"},
                "lab": {"type": "string", "description": "Filter by lab (IonQ, xAI, Anthropic, etc.)"},
            },
        },
    },
    {
        "name": "feedify_graph",
        "description": "Get the full frontier intelligence graph (persons, signals, convergences)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "feedify_chat",
        "description": "Chat with Feedify AI about any data",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Question or prompt"},
                "context": {"type": "string", "description": "Context: general, insiders, frontier"},
            },
            "required": ["message"],
        },
    },
    {
        "name": "feedify_feeds",
        "description": "List configured feeds",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "feedify_sources",
        "description": "List data sources and their status",
        "inputSchema": {"type": "object", "properties": {}},
    },
]
