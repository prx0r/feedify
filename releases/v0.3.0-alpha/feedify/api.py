from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from feedify.db import SessionLocal, init_db
from feedify.models import Feed, IngestionRun, Signal
from feedify.schemas import FeedCreate, FeedUpdate
from feedify.seed import seed
from feedify.services.feeds import feed_to_dict, feed_to_rss, icon_png, manifest, slugify
from feedify.services.ingestion import ADAPTERS, ingest_all
from feedify.services.mcp_remote import call_tool, list_tools, source_configs
from feedify.services.ranking import infer_algorithm_from_prompt
from feedify.settings import get_settings

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title="Feedify Alpha", version="0.1.0", lifespan=lifespan)


def _index_html(feed: Feed | None = None) -> str:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    title = feed.name if feed else "Feedify"
    manifest_tag = f'<link rel="manifest" href="/manifest/{feed.slug}.webmanifest">' if feed else ""
    apple_icon = f'<link rel="apple-touch-icon" href="/icon/{feed.slug}/192.png">' if feed else ""
    app_title = f'<meta name="apple-mobile-web-app-title" content="{title}">' if feed else ""
    return (
        html.replace("__TITLE__", title)
        .replace("__MANIFEST__", manifest_tag)
        .replace("__APPLE_ICON__", apple_icon)
        .replace("__APPLE_APP_TITLE__", app_title)
    )


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _index_html()


@app.get("/f/{slug}", response_class=HTMLResponse)
def feed_page(slug: str) -> str:
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed or not feed.public:
            raise HTTPException(404, "Feed not found")
        return _index_html(feed)


@app.get("/static/{path:path}")
def static_file(path: str):
    file = (STATIC / path).resolve()
    if STATIC.resolve() not in file.parents or not file.exists() or not file.is_file():
        raise HTTPException(404, "Asset not found")
    return FileResponse(file, media_type=mimetypes.guess_type(file.name)[0])


@app.get("/api/health")
def health() -> dict[str, Any]:
    with SessionLocal() as session:
        return {
            "status": "ok",
            "feeds": session.scalar(select(func.count()).select_from(Feed)) or 0,
            "signals": session.scalar(select(func.count()).select_from(Signal)) or 0,
            "x402": {"enabled": settings.x402_enabled, "configured": bool(settings.x402_pay_to)},
        }


@app.get("/api/sources")
def sources() -> list[dict[str, Any]]:
    configured = {
        "trustmrr": bool(settings.trustmrr_api_key),
        "glama": True,
        "github": True,
        "hackernews": True,
        "storeleads": bool(settings.storeleads_api_key),
        "appfigures": bool(settings.appfigures_username and settings.appfigures_password and settings.appfigures_client_key),
    }
    with SessionLocal() as session:
        runs = session.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(100)).all()
        latest: dict[str, IngestionRun] = {}
        for run in runs:
            latest.setdefault(run.source_type, run)
        return [
            {
                "name": name,
                "configured": configured.get(name, False),
                "last_run": (
                    {
                        "status": latest[name].status,
                        "fetched": latest[name].fetched,
                        "signals_created": latest[name].signals_created,
                        "started_at": latest[name].started_at.isoformat(),
                        "error": latest[name].error,
                    }
                    if name in latest
                    else None
                ),
            }
            for name in ADAPTERS
        ]


@app.post("/api/ingest")
async def ingest(payload: dict[str, Any] = Body(default_factory=dict)) -> list[dict[str, Any]]:
    requested = payload.get("sources") or list(ADAPTERS.keys())
    invalid = [x for x in requested if x not in ADAPTERS]
    if invalid:
        raise HTTPException(400, f"Unknown source(s): {', '.join(invalid)}")
    with SessionLocal() as session:
        runs = await ingest_all(session, requested, payload.get("limit"))
        return [
            {
                "source": r.source_type,
                "status": r.status,
                "fetched": r.fetched,
                "inserted": r.inserted,
                "signals_created": r.signals_created,
                "error": r.error,
            }
            for r in runs
        ]


@app.get("/api/signals")
def signals(limit: int = Query(100, ge=1, le=500), domain: str | None = None) -> list[dict[str, Any]]:
    with SessionLocal() as session:
        stmt = select(Signal).options(joinedload(Signal.record)).order_by(Signal.created_at.desc())
        if domain:
            stmt = stmt.where(Signal.domain == domain)
        rows = session.scalars(stmt.limit(limit)).all()
        return [
            {
                "id": s.id,
                "type": s.signal_type,
                "domain": s.domain,
                "title": s.title,
                "summary": s.summary,
                "why_it_matters": s.why_it_matters,
                "base_score": s.base_score,
                "tags": s.tags,
                "created_at": s.created_at.isoformat(),
                "source": {
                    "type": s.record.source_type,
                    "author": s.record.author,
                    "url": s.record.url,
                    "metrics": s.record.metrics,
                },
            }
            for s in rows
        ]


@app.get("/api/feeds")
def feeds() -> list[dict[str, Any]]:
    with SessionLocal() as session:
        rows = session.scalars(select(Feed).order_by(Feed.updated_at.desc())).all()
        return [
            {
                "slug": f.slug,
                "name": f.name,
                "description": f.description,
                "prompt": f.prompt,
                "icon": f.icon,
                "public": f.public,
                "weights": f.weights,
                "filters": f.filters,
            }
            for f in rows
        ]


@app.post("/api/feeds")
def create_feed(payload: FeedCreate) -> dict[str, Any]:
    with SessionLocal() as session:
        slug = slugify(payload.slug or payload.name)
        base_slug = slug
        i = 2
        while session.scalar(select(Feed).where(Feed.slug == slug)):
            slug = f"{base_slug}-{i}"
            i += 1
        inferred_weights, inferred_filters = infer_algorithm_from_prompt(payload.prompt)
        feed = Feed(
            slug=slug,
            name=payload.name,
            description=payload.description or payload.prompt,
            prompt=payload.prompt,
            public=payload.public,
            icon=payload.icon,
            weights=payload.weights or inferred_weights,
            filters=payload.filters or inferred_filters,
        )
        session.add(feed)
        session.commit()
        return {"slug": feed.slug, "url": f"{settings.feedify_public_base_url}/f/{feed.slug}"}


@app.patch("/api/feeds/{slug}")
def update_feed(slug: str, payload: FeedUpdate) -> dict[str, Any]:
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed:
            raise HTTPException(404, "Feed not found")
        data = payload.model_dump(exclude_none=True)
        if "prompt" in data and "weights" not in data and "filters" not in data:
            weights, filters = infer_algorithm_from_prompt(data["prompt"])
            data["weights"], data["filters"] = weights, filters
        for key, value in data.items():
            setattr(feed, key, value)
        session.commit()
        return {"ok": True, "slug": feed.slug}


@app.post("/api/feeds/{slug}/fork")
def fork_feed(slug: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    with SessionLocal() as session:
        source = session.scalar(select(Feed).where(Feed.slug == slug))
        if not source:
            raise HTTPException(404, "Feed not found")
        name = payload.get("name") or f"{source.name} Fork"
        new_slug = slugify(payload.get("slug") or name)
        i = 2
        base = new_slug
        while session.scalar(select(Feed).where(Feed.slug == new_slug)):
            new_slug = f"{base}-{i}"
            i += 1
        clone = Feed(
            slug=new_slug,
            name=name,
            description=payload.get("description", source.description),
            prompt=payload.get("prompt", source.prompt),
            icon=payload.get("icon", source.icon),
            public=payload.get("public", True),
            weights=payload.get("weights", source.weights),
            filters=payload.get("filters", source.filters),
        )
        session.add(clone)
        session.commit()
        return {"slug": clone.slug, "url": f"{settings.feedify_public_base_url}/f/{clone.slug}"}


@app.get("/api/feeds/{slug}.json")
def feed_json(slug: str, limit: int = Query(50, ge=1, le=200)) -> JSONResponse:
    return JSONResponse(get_feed(slug, limit))


@app.get("/api/feeds/{slug}.rss")
def feed_rss(slug: str, limit: int = Query(50, ge=1, le=200)) -> Response:
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed or not feed.public:
            raise HTTPException(404, "Feed not found")
        return Response(
            feed_to_rss(session, feed, settings.feedify_public_base_url, limit),
            media_type="application/rss+xml; charset=utf-8",
        )


@app.get("/manifest/{slug}.webmanifest")
def feed_manifest(slug: str) -> JSONResponse:
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug, Feed.public.is_(True)))
        if not feed:
            raise HTTPException(404, "Feed not found")
        return JSONResponse(manifest(feed, settings.feedify_public_base_url), media_type="application/manifest+json")


@app.get("/icon/{slug}/{size}.png")
def feed_icon(slug: str, size: int) -> Response:
    if size not in (180, 192, 512):
        raise HTTPException(400, "Supported sizes: 180, 192, 512")
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug, Feed.public.is_(True)))
        if not feed:
            raise HTTPException(404, "Feed not found")
        return Response(icon_png(feed, size), media_type="image/png")


@app.get("/api/feeds/{slug}")
def get_feed(slug: str, limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed or not feed.public:
            raise HTTPException(404, "Feed not found")
        return feed_to_dict(session, feed, limit)


@app.get("/api/paid/feeds/{slug}.json")
def paid_feed_json(slug: str, limit: int = Query(50, ge=1, le=200)) -> JSONResponse:
    # The route is ordinary JSON unless X402_ENABLED=true, when middleware gates it.
    return JSONResponse(get_feed(slug, limit))


@app.get("/api/mcp/sources")
def mcp_sources() -> list[dict[str, Any]]:
    return [{"name": c.get("name"), "url": c.get("url"), "configured": True} for c in source_configs()]


@app.get("/api/mcp/{name}/tools")
async def mcp_tools(name: str) -> list[dict[str, Any]]:
    try:
        return await list_tools(name)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(501, str(exc)) from exc


@app.post("/api/mcp/{name}/call")
async def mcp_call(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    tool_name = payload.get("tool")
    if not tool_name:
        raise HTTPException(400, "tool is required")
    try:
        return await call_tool(name, tool_name, payload.get("arguments") or {})
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(501, str(exc)) from exc


# Install optional payment middleware only after all routes are declared.
from feedify.x402 import install_x402
install_x402(app)
