"""Feedify MCP Server — Model Context Protocol for Feedify 2.0 intelligence.

Allows AI assistants to query Feedify data directly.
Supports both tools (imperative) and resources ( subscribable delta feeds).
"""
from __future__ import annotations

import json
from typing import Any

import httpx

FEEDIFY_BASE = "https://v2.feedify.egoic.ai"


async def call_tool(tool: str, args: dict[str, Any]) -> Any:
    """Call a Feedify MCP tool."""
    async with httpx.AsyncClient() as client:
        if tool == "feedify_health":
            r = await client.get(f"{FEEDIFY_BASE}/api/health", timeout=10)
            return r.json()

        elif tool == "feedify_objects":
            limit = args.get("limit", 20)
            domain = args.get("domain")
            kind = args.get("kind")
            url = f"{FEEDIFY_BASE}/api/objects?limit={limit}"
            if domain:
                url += f"&domain={domain}"
            if kind:
                url += f"&kind={kind}"
            r = await client.get(url, timeout=10)
            return r.json()

        elif tool == "feedify_insiders":
            limit = args.get("limit", 20)
            r = await client.get(f"{FEEDIFY_BASE}/api/insiders?limit={limit}", timeout=10)
            return r.json()

        elif tool == "feedify_frontier":
            limit = args.get("limit", 20)
            domain = args.get("domain")
            url = f"{FEEDIFY_BASE}/api/frontier?limit={limit}"
            if domain:
                url += f"&domain={domain}"
            r = await client.get(url, timeout=10)
            return r.json()

        elif tool == "feedify_graph":
            limit = args.get("limit", 500)
            r = await client.get(f"{FEEDIFY_BASE}/api/graph?limit={limit}", timeout=15)
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

        elif tool == "feedify_compiled_feed":
            slug = args.get("slug", "")
            user_id = args.get("user_id", "mcp-agent")
            limit = args.get("limit", 20)
            r = await client.get(f"{FEEDIFY_BASE}/api/feeds/{slug}/compiled?user_id={user_id}&limit={limit}", timeout=15)
            return r.json()

        elif tool == "feedify_delta":
            slug = args.get("slug", "")
            user_id = args.get("user_id", "mcp-agent")
            limit = args.get("limit", 20)
            r = await client.get(f"{FEEDIFY_BASE}/api/feeds/{slug}/delta?user_id={user_id}&limit={limit}", timeout=15)
            return r.json()

        elif tool == "feedify_import_chatgpt":
            text = args.get("text", "")
            title = args.get("title", "MCP import")
            r = await client.post(f"{FEEDIFY_BASE}/api/import/chatgpt", json={"text": text, "title": title}, timeout=30)
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
        "name": "feedify_objects",
        "description": "List objects from the knowledge graph (entities, theories, decisions, picks, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of objects to return (default 20)"},
                "domain": {"type": "string", "description": "Filter by domain (quantum, agents, insiders, commerce, etc.)"},
                "kind": {"type": "string", "description": "Filter by kind (entity, person, company, theory, pick, decision, etc.)"},
            },
        },
    },
    {
        "name": "feedify_insiders",
        "description": "List insider trading decisions and claims from the knowledge graph",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of items to return (default 20)"},
            },
        },
    },
    {
        "name": "feedify_frontier",
        "description": "List frontier objects from the knowledge graph",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of objects to return (default 20)"},
                "domain": {"type": "string", "description": "Filter by domain"},
            },
        },
    },
    {
        "name": "feedify_graph",
        "description": "Get the full knowledge graph (objects, edges, relationships)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max objects to include (default 500)"},
            },
        },
    },
    {
        "name": "feedify_chat",
        "description": "Chat with Feedify AI about the knowledge graph",
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
        "description": "List configured feed algorithms",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "feedify_sources",
        "description": "List data sources and their status",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "feedify_compiled_feed",
        "description": "Run a compiled multi-stage feed: candidate retrieval → semantic → delta → diversity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Feed slug"},
                "user_id": {"type": "string", "description": "User ID for delta tracking (default: mcp-agent)"},
                "limit": {"type": "integer", "description": "Max items (default 20)"},
            },
            "required": ["slug"],
        },
    },
    {
        "name": "feedify_delta",
        "description": "Get delta feed: only what changed since user last saw each object version",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Feed slug"},
                "user_id": {"type": "string", "description": "User ID for delta tracking"},
                "limit": {"type": "integer", "description": "Max items (default 20)"},
            },
            "required": ["slug"],
        },
    },
    {
        "name": "feedify_import_chatgpt",
        "description": "Import a ChatGPT conversation and compile it into the knowledge graph",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Full conversation text"},
                "title": {"type": "string", "description": "Conversation title"},
            },
            "required": ["text"],
        },
    },
]
