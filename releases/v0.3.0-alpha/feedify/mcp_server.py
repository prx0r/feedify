from __future__ import annotations

from sqlalchemy import select

from fish.db import SessionLocal, init_db
from fish.models import Feed
from fish.services.feeds import feed_to_dict


def build_server():
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise RuntimeError('Feedify MCP requires: uv sync --extra mcp') from exc

    mcp = MCPServer(
        "Feedify",
        instructions="Personal signal compiler. Use list_feeds, get_feed and search_feed to retrieve high-signal intelligence.",
    )

    @mcp.tool()
    def list_feeds() -> list[dict[str, str]]:
        """List all public Feedify feeds."""
        with SessionLocal() as session:
            feeds = session.scalars(select(Feed).where(Feed.public.is_(True)).order_by(Feed.name)).all()
            return [{"slug": f.slug, "name": f.name, "description": f.description} for f in feeds]

    @mcp.tool()
    def get_feed(slug: str, limit: int = 20) -> dict:
        """Get ranked signals from a public feed."""
        with SessionLocal() as session:
            feed = session.scalar(select(Feed).where(Feed.slug == slug, Feed.public.is_(True)))
            if not feed:
                return {"error": "feed not found"}
            return feed_to_dict(session, feed, min(max(limit, 1), 100))

    @mcp.tool()
    def search_feed(slug: str, query: str, limit: int = 10) -> dict:
        """Search the already-ranked items in a Feedify feed."""
        with SessionLocal() as session:
            feed = session.scalar(select(Feed).where(Feed.slug == slug, Feed.public.is_(True)))
            if not feed:
                return {"error": "feed not found"}
            data = feed_to_dict(session, feed, 200)
            q = query.lower()
            items = [
                item for item in data["items"]
                if q in (item["title"] + " " + item["summary"] + " " + " ".join(item["tags"])).lower()
            ][: min(max(limit, 1), 50)]
            return {"feed": data["feed"], "query": query, "items": items}

    return mcp


mcp = None
try:
    mcp = build_server()
except RuntimeError:
    pass


def main() -> None:
    init_db()
    server = mcp or build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
