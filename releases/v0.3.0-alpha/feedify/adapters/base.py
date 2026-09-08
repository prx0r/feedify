from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from feedify.schemas import NormalizedItem


class SourceAdapter(ABC):
    name: str

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client or httpx.AsyncClient(timeout=30, follow_redirects=True)
        self._owns_client = client is None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        if self._owns_client:
            await self.client.aclose()

    @property
    def configured(self) -> bool:
        return True

    @abstractmethod
    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        raise NotImplementedError
