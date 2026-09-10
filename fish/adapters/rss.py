from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from typing import Iterable

from fish.schemas import NormalizedItem

from .base import SourceAdapter
from .utils import parse_datetime


class RSSAdapter(SourceAdapter):
    name = "rss"

    def __init__(self, urls: Iterable[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.urls = list(urls)

    async def fetch(self, limit: int = 25) -> list[NormalizedItem]:
        out: list[NormalizedItem] = []
        for url in self.urls:
            if len(out) >= limit:
                break
            response = await self.client.get(url)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            rows = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for node in rows:
                if len(out) >= limit:
                    break
                def text(name: str) -> str | None:
                    el = node.find(name)
                    return el.text.strip() if el is not None and el.text else None

                title = text("title") or text("{http://www.w3.org/2005/Atom}title") or "Untitled"
                link = text("link")
                if not link:
                    link_el = node.find("{http://www.w3.org/2005/Atom}link")
                    link = link_el.attrib.get("href") if link_el is not None else None
                guid = text("guid") or text("{http://www.w3.org/2005/Atom}id") or link or title
                description = text("description") or text("{http://www.w3.org/2005/Atom}summary")
                date = text("pubDate") or text("{http://www.w3.org/2005/Atom}updated")
                out.append(
                    NormalizedItem(
                        source_type=self.name,
                        external_id=hashlib.sha1(str(guid).encode()).hexdigest(),
                        title=title,
                        url=link,
                        body=description,
                        published_at=parse_datetime(date),
                        metrics={"feed_url": url},
                        raw={"guid": guid, "feed_url": url},
                    )
                )
        return out
