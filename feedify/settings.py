from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    feedify_database_url: str = "sqlite:///./feedify.db"
    feedify_public_base_url: str = "http://localhost:8000"
    feedify_ingest_limit: int = 25

    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek/deepseek-chat-v3-0324"

    trustmrr_api_key: str = ""
    storeleads_api_key: str = ""
    appfigures_username: str = ""
    appfigures_password: str = ""
    appfigures_client_key: str = ""
    github_token: str = ""
    apify_token: str = ""
    getxapi_key: str = ""
    getxapi_backup_key: str = ""
    getxapi_watchlist_path: str = "config/insiders_watchlist.json"
    getxapi_per_handle_count: int = 5
    getxapi_max_handles: int = 20

    mcp_sources_json: str = "[]"

    x402_enabled: bool = False
    x402_pay_to: str = ""
    x402_network: str = "eip155:84532"
    x402_facilitator_url: str = "https://x402.org/facilitator"
    x402_price_usd: float = 0.01

    @property
    def mcp_sources(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self.mcp_sources_json)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


@lru_cache
def get_settings() -> Settings:
    return Settings()
