from __future__ import annotations

import os
from typing import Any

from feedify.settings import get_settings


def source_configs() -> list[dict[str, Any]]:
    configs = list(get_settings().mcp_sources)
    # Useful presets: included automatically if their credentials exist.
    settings = get_settings()

    # TrustMRR supports authenticated MCP plus a bounded public discovery endpoint.
    if not any(x.get("name") in {"trustmrr", "trustmrr-discovery"} for x in configs):
        if settings.trustmrr_api_key:
            configs.append({
                "name": "trustmrr",
                "url": "https://trustmrr.com/api/mcp",
                "bearer_env": "TRUSTMRR_API_KEY",
            })
        else:
            configs.append({
                "name": "trustmrr-discovery",
                "url": "https://trustmrr.com/api/mcp/discovery",
            })

    if settings.storeleads_api_key and not any(x.get("name") == "storeleads" for x in configs):
        configs.append({
            "name": "storeleads",
            "url": "https://storeleads.app/mcp",
            "bearer_env": "STORELEADS_API_KEY",
        })

    # Apify exposes a hosted Streamable-HTTP MCP endpoint. Anonymous discovery
    # tools are useful even without a token; authenticated use unlocks Actors.
    if not any(x.get("name") in {"apify", "apify-discovery"} for x in configs):
        if settings.apify_token:
            configs.append({
                "name": "apify",
                "url": "https://mcp.apify.com",
                "bearer_env": "APIFY_TOKEN",
            })
        else:
            configs.append({
                "name": "apify-discovery",
                "url": "https://mcp.apify.com?tools=search-actors,fetch-actor-details,search-apify-docs,fetch-apify-docs",
            })
    return configs


def _config(name: str) -> dict[str, Any]:
    for config in source_configs():
        if config.get("name") == name:
            return config
    raise KeyError(f"Unknown MCP source: {name}")


async def _with_client(name: str, callback):
    try:
        import httpx2
        from mcp import Client
        from mcp.client.streamable_http import streamable_http_client
    except ImportError as exc:
        raise RuntimeError('Remote MCP support requires: uv sync --extra mcp') from exc

    config = _config(name)
    headers = dict(config.get("headers") or {})
    bearer_env = config.get("bearer_env")
    if bearer_env and os.getenv(bearer_env):
        headers["Authorization"] = f"Bearer {os.environ[bearer_env]}"
    async with httpx2.AsyncClient(
        headers=headers,
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client(config["url"], http_client=http_client)
        async with Client(transport) as client:
            return await callback(client)


async def list_tools(name: str) -> list[dict[str, Any]]:
    async def cb(client):
        result = await client.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None),
            }
            for tool in result.tools
        ]

    return await _with_client(name, cb)


async def call_tool(name: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    async def cb(client):
        result = await client.call_tool(tool_name, arguments)
        return {
            "is_error": bool(getattr(result, "is_error", False)),
            "structured_content": getattr(result, "structured_content", None),
            "content": [
                c.model_dump(mode="json") if hasattr(c, "model_dump") else str(c)
                for c in (getattr(result, "content", None) or [])
            ],
        }

    return await _with_client(name, cb)
