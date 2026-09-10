from __future__ import annotations

import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from feedify.db import SessionLocal, init_db
from feedify.models import Feed, FeedVersion, IngestionRun, Object, Edge, Interaction, Artifact
from feedify.schemas import FeedCreate, FeedUpdate
from feedify.seed import seed
from feedify.services.feeds import feed_to_dict, feed_to_rss, get_delta_feed, icon_png, manifest, slugify
from feedify.services.ingestion import ADAPTERS, ingest_all
from feedify.services.mcp_remote import call_tool, list_tools, source_configs
from feedify.services.minimal_graph import build_graph_from_db
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

# Include ML routes
from .ml_routes import router as ml_router
app.include_router(ml_router)

# Include Reality Feed routes
from .reality_routes import router as reality_router
app.include_router(reality_router)


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


@app.get("/reality", response_class=HTMLResponse)
def reality_page() -> str:
    return (STATIC / "reality.html").read_text(encoding="utf-8")


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
            "version": "2.0.0-alpha",
            "feeds": session.scalar(select(func.count()).select_from(Feed)) or 0,
            "objects": session.scalar(select(func.count()).select_from(Object)) or 0,
            "edges": session.scalar(select(func.count()).select_from(Edge)) or 0,
            "artifacts": session.scalar(select(func.count()).select_from(Artifact)) or 0,
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
@app.get("/api/objects")
def objects_list(limit: int = Query(100, ge=1, le=500), domain: str | None = None, kind: str | None = None) -> list[dict[str, Any]]:
    with SessionLocal() as session:
        stmt = select(Object).order_by(Object.created_at.desc())
        if domain:
            stmt = stmt.where(Object.domain == domain)
        if kind:
            stmt = stmt.where(Object.kind == kind)
        rows = session.scalars(stmt.limit(limit)).all()
        return [
            {
                "id": o.id,
                "object_key": o.object_key,
                "kind": o.kind,
                "version": o.version,
                "domain": o.domain,
                "title": o.title,
                "summary": o.summary,
                "confidence": o.confidence,
                "tags": (o.metadata_json or {}).get("tags", []),
                "created_at": o.created_at.isoformat(),
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            }
            for o in rows
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
        feed.version += 1
        # Save version snapshot
        session.add(FeedVersion(
            feed_id=feed.id,
            version=feed.version,
            prompt=feed.prompt,
            weights=feed.weights,
            filters=feed.filters,
        ))
        session.commit()
        return {"ok": True, "slug": feed.slug, "version": feed.version}


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
            forked_from_id=source.id,
            creator_id=payload.get("creator_id", "user"),
        )
        session.add(clone)
        session.flush()
        # Save initial version
        session.add(FeedVersion(
            feed_id=clone.id,
            version=1,
            prompt=clone.prompt,
            weights=clone.weights,
            filters=clone.filters,
        ))
        session.commit()
        return {"slug": clone.slug, "forked_from": source.slug, "url": f"{settings.feedify_public_base_url}/f/{clone.slug}"}


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


@app.get("/api/feeds/{slug}/brief")
def feed_brief(slug: str, limit: int = Query(10, ge=1, le=50)) -> dict[str, Any]:
    """Clustered alpha digest: stories (deduped), implied tickers with
    1d moves, corroboration + unmoved bonuses. Deterministic, no LLM key needed."""
    from feedify.services.brief import build_brief
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed or not feed.public:
            raise HTTPException(404, "Feed not found")
        return build_brief(session, feed, limit)


@app.get("/api/feeds/{slug}/brief.txt")
def feed_brief_text(slug: str, limit: int = Query(10, ge=1, le=50)) -> Response:
    """Plain-text digest for scrolling: ordered alpha, no UI needed."""
    from feedify.services.brief import build_brief, synthesize_brief
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed or not feed.public:
            raise HTTPException(404, "Feed not found")
        return Response(synthesize_brief(build_brief(session, feed, limit)),
                        media_type="text/plain; charset=utf-8")


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


# ── MCP Server ───────────────────────────────────────────────────────────────

@app.get("/api/mcp/tools")
async def mcp_tools():
    """List available MCP tools."""
    from feedify.mcp_server import TOOLS
    return TOOLS


@app.post("/api/mcp/call")
async def mcp_call(payload: dict[str, Any]):
    """Call an MCP tool."""
    from feedify.mcp_server import call_tool
    tool = payload.get("tool", "")
    args = payload.get("args", {})
    if not tool:
        raise HTTPException(400, "tool is required")
    result = await call_tool(tool, args)
    return result


# ── Frontier Intelligence ────────────────────────────────────────────────────

@app.get("/frontier", response_class=HTMLResponse)
def frontier_page() -> str:
    """Quantum × AGI frontier intelligence dashboard."""
    return (STATIC / "frontier.html").read_text(encoding="utf-8")


@app.get("/api/frontier")
def frontier_signals(
    limit: int = Query(100, ge=1, le=500),
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """Frontier objects from the knowledge graph."""
    with SessionLocal() as session:
        query = select(Object).order_by(Object.confidence.desc())
        if domain:
            query = query.where(Object.domain == domain)
        rows = session.scalars(query.limit(limit)).all()
        return [
            {
                "id": o.id,
                "object_key": o.object_key,
                "kind": o.kind,
                "domain": o.domain,
                "title": o.title,
                "summary": o.summary,
                "confidence": o.confidence,
                "tags": (o.metadata_json or {}).get("tags", []),
                "created_at": o.created_at.isoformat(),
            }
            for o in rows
        ]

        results = []
        for s in rows:
            if not s.record:
                continue

            # Check if author is in our watchlist
            author_handle = s.record.author or ""
            metrics = s.record.metrics or {}
            author_handle_str = str(metrics.get("author_handle", author_handle))
            author_lower = author_handle_str.lower()

            # Try to find in watchlist by handle
            account_info = None
            for handle, info in account_map.items():
                if handle in author_lower or author_lower in handle:
                    account_info = info
                    break

            if not account_info:
                continue

            # Score the signal
            text = f"{s.title or ''} {s.summary or ''}"
            is_reply = metrics.get("is_reply", False)

            score_result = score_quantum_agi_signal(
                text=text,
                author_handle=author_handle_str,
                account_info=account_info,
                is_reply=is_reply,
                metrics=metrics,
            )

            results.append({
                "id": s.id,
                "title": s.title,
                "summary": s.summary[:300] if s.summary else "",
                "score": score_result["score"],
                "tier": score_result["tier"],
                "signal_type": score_result["signal_type"],
                "breakdown": score_result["breakdown"],
                "tech_terms": score_result.get("tech_terms", 0),
                "domains_present": score_result.get("domains_present", 0),
                "author": author_handle,
                "lab": account_info.get("lab", ""),
                "priority": account_info.get("priority", ""),
                "role": account_info.get("role", ""),
                "url": s.record.url,
                "is_reply": is_reply,
                "tags": s.tags,
                "domain": s.domain,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        # Apply filters
        if signal_type:
            results = [r for r in results if r["signal_type"] == signal_type]
        if lab:
            results = [r for r in results if r["lab"] == lab]

        return results[:limit]


@app.get("/api/frontier/graph")
def frontier_graph_endpoint(limit: int = Query(500, ge=1, le=2000)) -> dict[str, Any]:
    """Get the frontier intelligence graph."""
    from feedify.services.frontier_graph import build_minimal_graph, graph_to_json

    with SessionLocal() as session:
        graph = build_minimal_graph(session, limit=limit)
        return graph_to_json(graph)


@app.get("/api/theses")
def list_theses():
    """List all theses."""
    from feedify.services.thesis_engine import load_theses
    return load_theses()


@app.get("/api/theses/{thesis_id}")
def get_thesis(thesis_id: str):
    """Get a specific thesis."""
    from feedify.services.thesis_engine import load_theses
    theses = load_theses()
    for t in theses:
        if t.get("id") == thesis_id:
            return t
    raise HTTPException(404, "Thesis not found")


@app.post("/api/theses/synthesize")
def synthesize_thesis_endpoint():
    """Synthesize a new thesis or update an existing one."""
    from feedify.services.thesis_engine import synthesize_thesis, save_thesis, append_to_thesis
    from feedify.services.frontier_graph import build_minimal_graph
    
    with SessionLocal() as session:
        graph = build_minimal_graph(session, limit=200)
    
    # Get recent evidence
    recent = []
    with SessionLocal() as session:
        stmt = select(Object).order_by(Object.created_at.desc()).limit(50)
        rows = session.scalars(stmt).all()
        for o in rows:
            recent.append({
                "id": str(o.id),
                "title": o.title,
                "domain": o.domain,
                "kind": o.kind,
            })
    
    result = synthesize_thesis(graph, recent)
    if not result:
        return {"action": "none", "message": "No new thesis warranted"}
    
    if result.get("action") == "create":
        thesis = {
            "id": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            "title": result.get("title", "Untitled"),
            "statement": result.get("statement", ""),
            "implications": result.get("implications", ""),
            "falsification": result.get("falsification", ""),
            "confidence": result.get("confidence", 0.5),
            "evidence_ids": result.get("evidence_ids", []),
            "evidence_count": len(result.get("evidence_ids", [])),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        save_thesis(thesis)
        return {"action": "created", "thesis": thesis}
    
    elif result.get("action") == "update":
        thesis_id = result.get("thesis_id")
        if thesis_id:
            thesis = append_to_thesis(thesis_id, recent[:10])
            return {"action": "updated", "thesis": thesis}
    
    return {"action": "none", "message": "No update warranted"}


# ── Stock Thesis Tracking ─────────────────────────────────────────────────────

@app.get("/api/stocks")
def list_stocks():
    """List all tracked stocks with thesis alignment."""
    from feedify.services.stock_registry import STOCK_REGISTRY
    return STOCK_REGISTRY


@app.get("/api/stocks/data")
def stocks_data(tickers: str = Query("")):
    """Fetch current market data for stocks."""
    from feedify.services.stock_registry import get_stock_data
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        ticker_list = ["SVCO", "LEU", "EROC", "SDGR", "GSIT", "MOD", "AMKR", "RXRX", "ALMU", "ONTO"]
    return get_stock_data(ticker_list)


@app.get("/api/stocks/report")
def stocks_report():
    """Generate comprehensive thesis vs market report."""
    from feedify.services.stock_registry import generate_stock_report
    return generate_stock_report()


@app.get("/api/stocks/{ticker}")
def stock_detail(ticker: str):
    """Get detailed stock info with thesis alignment."""
    from feedify.services.stock_registry import STOCK_REGISTRY, get_stock_data, get_thesis_alignment
    
    stock = next((s for s in STOCK_REGISTRY if s["ticker"] == ticker), None)
    if not stock:
        raise HTTPException(404, "Stock not found")
    
    market_data = get_stock_data([ticker])
    alignment = get_thesis_alignment(stock, market_data.get(ticker, {}))
    
    return {
        **stock,
        "market_data": market_data.get(ticker, {}),
        "alignment": alignment,
    }


# ── Insiders Intelligence ─────────────────────────────────────────────────────

@app.get("/insiders", response_class=HTMLResponse)
def insiders_page() -> str:
    """Insider intelligence dashboard."""
    return (STATIC / "insiders.html").read_text(encoding="utf-8")


@app.get("/api/insiders")
def insiders(
    limit: int = Query(100, ge=1, le=500),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    sector: str | None = None,
    kind: str | None = None,
) -> list[dict[str, Any]]:
    """Insider signals from the Object graph."""
    with SessionLocal() as session:
        query = select(Object).where(
            Object.kind.in_(["decision", "claim"]),
        )
        if sector:
            query = query.where(Object.domain == sector.lower())
        if kind:
            query = query.where(Object.kind == kind)
        query = query.order_by(Object.confidence.desc()).limit(limit)

        rows = session.scalars(query).all()
        return [
            {
                "id": o.id,
                "object_key": o.object_key,
                "kind": o.kind,
                "domain": o.domain,
                "title": o.title,
                "summary": o.summary,
                "confidence": o.confidence,
                "tags": (o.metadata_json or {}).get("tags", []),
                "metadata": o.metadata_json,
                "created_at": o.created_at.isoformat(),
            }
            for o in rows
        ]


@app.get("/api/insiders/stats")
def insiders_stats() -> dict[str, Any]:
    """Object graph statistics."""
    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(Object)) or 0
        domains = {}
        for row in session.scalars(select(Object.domain, func.count()).group_by(Object.domain)).all():
            domains[row[0]] = row[1]
        kinds = {}
        for row in session.scalars(select(Object.kind, func.count()).group_by(Object.kind)).all():
            kinds[row[0]] = row[1]
        return {"total_objects": total, "domains": domains, "kinds": kinds}


@app.get("/api/insiders/summary")
async def insiders_summary() -> dict[str, Any]:
    """AI-generated summary of highest confidence objects."""
    with SessionLocal() as session:
        rows = session.scalars(
            select(Object).order_by(Object.confidence.desc()).limit(50)
        ).all()
        objects = [
            {"title": o.title, "summary": o.summary, "confidence": o.confidence, "kind": o.kind, "domain": o.domain}
            for o in rows
        ]
    return {"objects": objects, "count": len(objects)}


@app.post("/api/insiders/chat")
async def insiders_chat(payload: dict[str, Any]) -> dict[str, str]:
    """Chat about the knowledge graph with AI."""
    message = payload.get("message", "")
    if not message:
        raise HTTPException(400, "message is required")

    with SessionLocal() as session:
        graph = build_graph_from_db(session, limit=200)
        graph_context = graph.to_llm_context()

    system_prompt = f"""You are Feedify AI — an intelligence analyst with access to the knowledge graph.

KNOWLEDGE GRAPH:
{graph_context[:8000]}

RULES:
- Be direct and opinionated
- Reference specific objects by title and kind
- Identify patterns and connections across the graph
- Focus on ACTIONABLE intelligence"""

    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]

    settings = get_settings()
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    api_key = settings.llm_api_key or ""

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "mimo-v2.5", "messages": messages, "max_tokens": 1500, "temperature": 0.4}, timeout=30)
            if resp.status_code != 200:
                return {"response": f"AI temporarily unavailable (HTTP {resp.status_code})."}
            data = resp.json()
            return {"response": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"response": f"AI error: {e}"}


# ── Unified AI Chat ──────────────────────────────────────────────────────────

@app.post("/api/chat")
async def unified_chat(payload: dict[str, Any]) -> dict[str, str]:
    """Unified chat endpoint with access to all Feedify data."""
    message = payload.get("message", "")
    history = payload.get("history", [])
    context = payload.get("context", "general")  # "insiders", "feed", "frontier", "general"

    if not message:
        raise HTTPException(400, "message is required")

    # Gather all relevant data
    with SessionLocal() as session:
        # Build frontier graph if context is frontier
        if context == "frontier":
            from feedify.services.frontier_graph import build_minimal_graph, graph_to_llm_context
            graph = build_minimal_graph(session, limit=200)
            graph_context = graph_to_llm_context(graph)
            person_count = len([e for e in graph.entities.values() if e.entity_type == "person"])
            lab_count = len(set(e.metadata.get("lab", "") for e in graph.entities.values() if e.entity_type == "person" and e.metadata.get("lab")))
        else:
            graph_context = None

        # Get recent objects
        objects = session.scalars(
            select(Object).order_by(Object.created_at.desc()).limit(100)
        ).all()

        # Get feeds
        feeds = session.scalars(select(Feed)).all()

        # Get source status
        sources = session.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(20)).all()

        # Build context
        object_data = [
            {
                "title": o.title,
                "summary": o.summary[:200] if o.summary else "",
                "domain": o.domain,
                "confidence": o.confidence,
                "kind": o.kind,
                "tags": (o.metadata_json or {}).get("tags", []),
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in objects
        ]

        feed_data = [{"name": f.name, "slug": f.slug, "prompt": f.prompt[:100]} for f in feeds]
        source_data = [{"type": s.source_type, "status": s.status, "fetched": s.fetched} for s in sources]

    # Build prompt
    context_str = json.dumps(object_data[:30], indent=2)
    feeds_str = json.dumps(feed_data, indent=2)
    sources_str = json.dumps(source_data, indent=2)

    if graph_context:
        system_prompt = f"""You are Feedify AI — an intelligence analyst with access to ALL Feedify data.

COMPLETE DATA:
{graph_context}

INSIDER SIGNALS:
- 12 verified insider transactions (OpenInsider/SEC)
- Key tickers: O (Realty Income) with multiple director sales

FEEDS:
- 6 configured feeds, 500+ signals total
- 9 data sources (X, OpenInsider, GitHub, HN, etc.)

You have real data from {person_count} researchers across {lab_count} labs.

ANALYSIS APPROACH:
- Do NOT use hardcoded rules or keywords
- Read the actual signals and people data
- Identify patterns fresh from the data each time
- Detect convergences by finding when multiple labs discuss related topics
- Find implicit assumptions by noticing what people take for granted
- Track belief updates by noticing when language changes
- Surface what's genuinely interesting, not what matches predetermined categories
- Connect insights across domains (insiders + frontier + feeds)

THE THESIS:
The question is not "when will AGI arrive" or "when will quantum be useful."
It's: "When does AI start materially shortening the quantum-computer R&D feedback loop?"

Look for:
- Employees changing their beliefs about bottlenecks
- Technical vocabulary collisions (quantum + AI terms)
- Reply threads where researchers argue about approaches
- Low-follower accounts with high role proximity
- What people are NOT discussing (absence as signal)
- Insider activity in frontier stocks

RULES:
- Be direct and opinionated
- Reference specific people by handle and lab
- Reference specific signals by score and type
- Focus on ACTIONABLE intelligence, not noise
- Fresh analysis every time — no canned responses"""
    else:
        system_prompt = f"""You are Feedify AI — an intelligence analyst with access to all backend data.

AVAILABLE DATA:
- {len(signals)} signals from {len(set(s.record.source_type for s in signals if s.record))} sources
- {len(feeds)} configured feeds
- Source ingestion status

SIGNALS (recent):
{context_str}

FEEDS:
{feeds_str}

SOURCES:
{sources_str}

CAPABILITIES:
- Answer questions about any signal, ticker, or insider activity
- Explain what signals mean and why they matter
- Compare sources and their reliability
- Identify patterns across signals
- Explain the scoring methodology

RULES:
- Be direct and opinionated
- Reference specific data from the signals
- If asked about a ticker, search the signals for it
- If asked about a source, reference the source data
- Distinguish verified data from X discovery"""


    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": message})

    settings = get_settings()
    
    # OpenCode Go endpoint
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    api_key = settings.llm_api_key or "sk-A5QHR5MRtUNec7BWqiRsZ0GAYck0CRT2Movsk7Q6U3UwcV77Y6G3TMXOhhyKh855"
    model = "mimo-v2.5"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "x-opencode-session": "feedify-chat",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.4,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return {"response": f"AI temporarily unavailable (HTTP {resp.status_code})."}
            data = resp.json()
            return {"response": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"response": f"AI error: {e}"}


# --- Delta Feed & Interaction Endpoints (Vision 2.0) ---

@app.get("/api/feeds/{slug}/delta")
def delta_feed(slug: str, user_id: str = Query("demo"), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """Delta feed: only objects that have changed since user last saw them."""
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed:
            raise HTTPException(404, "Feed not found")
        items = get_delta_feed(session, feed, user_id, limit)
        return {
            "feed": {"slug": feed.slug, "name": feed.name, "icon": feed.icon},
            "user_id": user_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "items": items,
        }


@app.post("/api/interactions")
def record_interaction(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Record a user interaction with an object (DONE/SAVE/FOLLOW/NOISE/seen)."""
    user_id = payload.get("user_id", "demo")
    object_id = payload.get("object_id")
    object_version = payload.get("object_version", 1)
    action = payload.get("action", "seen")
    feed_id = payload.get("feed_id")

    if not object_id:
        raise HTTPException(400, "object_id required")
    if action not in ("DONE", "SAVE", "FOLLOW", "NOISE", "seen"):
        raise HTTPException(400, f"Invalid action: {action}")

    with SessionLocal() as session:
        obj = session.get(Object, object_id)
        if not obj:
            raise HTTPException(404, "Object not found")

        existing = session.scalar(
            select(Interaction).where(
                Interaction.user_id == user_id,
                Interaction.object_id == object_id,
            )
        )
        if existing:
            existing.action = action
            existing.object_version = object_version
            if feed_id:
                existing.feed_id = feed_id
        else:
            session.add(Interaction(
                user_id=user_id,
                object_id=object_id,
                object_version=object_version,
                action=action,
                feed_id=feed_id,
            ))
        session.commit()
        return {"ok": True, "action": action, "object_id": object_id}


@app.get("/api/graph")
def graph_endpoint(limit: int = Query(500, ge=1, le=2000)) -> dict[str, Any]:
    """Get the knowledge graph as Object + Edge."""
    with SessionLocal() as session:
        graph = build_graph_from_db(session, limit)
        return {
            "entities": len(graph.entities),
            "connections": len(graph.connections),
            "llm_context": graph.to_llm_context(),
        }


@app.get("/api/objects/{object_id}")
def object_detail(object_id: int) -> dict[str, Any]:
    """Get a single object with its edges."""
    with SessionLocal() as session:
        obj = session.get(Object, object_id)
        if not obj:
            raise HTTPException(404, "Object not found")
        outgoing = session.scalars(
            select(Edge).where(Edge.source_id == object_id)
        ).all()
        incoming = session.scalars(
            select(Edge).where(Edge.target_id == object_id)
        ).all()
        return {
            "id": obj.id,
            "object_key": obj.object_key,
            "kind": obj.kind,
            "version": obj.version,
            "domain": obj.domain,
            "title": obj.title,
            "summary": obj.summary,
            "confidence": obj.confidence,
            "metadata": obj.metadata_json,
            "created_at": obj.created_at.isoformat(),
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
            "outgoing_edges": [
                {"target_id": e.target_id, "relation": e.relation, "weight": e.weight}
                for e in outgoing
            ],
            "incoming_edges": [
                {"source_id": e.source_id, "relation": e.relation, "weight": e.weight}
                for e in incoming
            ],
        }


# ── Compiled Feed Pipeline (Vision 2.0) ─────────────────────────────────────

@app.get("/api/feeds/{slug}/compiled")
async def compiled_feed(slug: str, user_id: str = Query("demo"), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """Multi-stage compiled feed: candidate retrieval → semantic → delta → diversity."""
    from feedify.services.compiled_feed import get_compiled_feed
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed:
            raise HTTPException(404, "Feed not found")
        items = await get_compiled_feed(session, feed, user_id, limit)
        return {
            "feed": {"slug": feed.slug, "name": feed.name, "icon": feed.icon},
            "user_id": user_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "items": items,
        }


@app.get("/api/feeds/{slug}/delta-compiled")
async def delta_compiled_feed(slug: str, user_id: str = Query("demo"), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """Delta compiled feed with new/updated separation."""
    from feedify.services.compiled_feed import get_delta_compiled_feed
    with SessionLocal() as session:
        feed = session.scalar(select(Feed).where(Feed.slug == slug))
        if not feed:
            raise HTTPException(404, "Feed not found")
        return await get_delta_compiled_feed(session, feed, user_id, limit)


# ── ChatGPT Importer (Vision 2.0) ───────────────────────────────────────────

@app.post("/api/import/chatgpt")
async def import_chatgpt(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Import a ChatGPT conversation and compile it into the knowledge graph.
    Accepts: { "title": "...", "messages": [{"role": "user/assistant", "content": "..."}] }
    Or: { "text": "full conversation text" }
    """
    from feedify.services.chatgpt_importer import import_conversation

    messages = payload.get("messages")
    text = payload.get("text")
    title = payload.get("title", "Imported conversation")

    if not messages and not text:
        raise HTTPException(400, "Provide 'messages' array or 'text' string")

    with SessionLocal() as session:
        objects_created, edges_created = await import_conversation(session, messages=messages, text=text, title=title)
        session.commit()
        return {
            "ok": True,
            "objects_created": objects_created,
            "edges_created": edges_created,
        }


# ── Convergence Detection (Vision 2.0) ──────────────────────────────────────

@app.get("/api/convergence")
def convergence_detect(topic: str | None = None, days: int = Query(7, ge=1, le=90)) -> dict[str, Any]:
    """Detect convergence: multiple source_distance=0 accounts discussing same topic."""
    from datetime import timedelta
    from collections import defaultdict

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    with SessionLocal() as session:
        objects = session.scalars(
            select(Object).where(Object.created_at >= cutoff)
        ).all()

    # Group by topic and date
    by_topic_date = defaultdict(list)
    for obj in objects:
        date = (obj.metadata_json or {}).get("date", "")[:10]
        author = (obj.metadata_json or {}).get("author", "")
        sd = (obj.metadata_json or {}).get("source_distance", 3)
        for t in (obj.metadata_json or {}).get("topics", []):
            if topic and t != topic:
                continue
            by_topic_date[f"{t}:{date}"].append({
                "author": author,
                "source_distance": sd,
                "kind": obj.kind,
                "title": obj.title[:80],
            })

    # Find convergences (2+ different authors, same topic, same day)
    convergences = []
    for key, entries in by_topic_date.items():
        authors = set(e["author"] for e in entries if e["author"])
        experimenters = [e for e in entries if e["source_distance"] == 0]
        if len(authors) >= 2:
            topic_name, date = key.split(":", 1)
            convergences.append({
                "topic": topic_name,
                "date": date,
                "authors": list(authors),
                "total_posts": len(entries),
                "experimenter_posts": len(experimenters),
                "kinds": list(set(e["kind"] for e in entries)),
            })

    convergences.sort(key=lambda x: (-x["experimenter_posts"], -x["total_posts"]))

    return {
        "days": days,
        "total_objects": len(objects),
        "convergences": convergences[:50],
    }


@app.get("/api/predictions")
def predictions_with_evidence(limit: int = Query(20, ge=1, le=100)) -> list[dict[str, Any]]:
    """Get predictions with connected evidence for backtesting."""
    with SessionLocal() as session:
        predictions = session.scalars(
            select(Object).where(Object.kind == "prediction").order_by(Object.confidence.desc())
        ).all()

    # Build edge index
    with SessionLocal() as session:
        all_edges = session.scalars(select(Edge)).all()
        pred_edges = {}
        for e in all_edges:
            pred_edges.setdefault(e.target_id, []).append(e)

    results = []
    for pred in predictions[:limit]:
        edges = pred_edges.get(pred.id, [])
        supports = [e for e in edges if e.relation == "supports"]
        contradicts = [e for e in edges if e.relation == "contradicts"]

        results.append({
            "id": pred.id,
            "title": pred.title[:200],
            "author": (pred.metadata_json or {}).get("author", "?"),
            "date": (pred.metadata_json or {}).get("date", "?"),
            "confidence": pred.confidence,
            "supports": len(supports),
            "contradicts": len(contradicts),
            "total_evidence": len(edges),
        })

    return results


@app.get("/api/graph/stats")
def graph_stats() -> dict[str, Any]:
    """Knowledge graph statistics."""
    with SessionLocal() as session:
        total_objects = session.scalar(select(func.count()).select_from(Object)) or 0
        total_edges = session.scalar(select(func.count()).select_from(Edge)) or 0
        total_artifacts = session.scalar(select(func.count()).select_from(Artifact)) or 0

        # By kind
        kinds = {}
        for kind, count in session.execute(select(Object.kind, func.count(Object.id)).group_by(Object.kind)).all():
            kinds[kind] = count

        # By domain
        domains = {}
        for domain, count in session.execute(select(Object.domain, func.count(Object.id)).group_by(Object.domain)).all():
            domains[domain] = count

        # Edge types
        edge_types = {}
        for relation, count in session.execute(select(Edge.relation, func.count(Edge.id)).group_by(Edge.relation)).all():
            edge_types[relation] = count

        return {
            "artifacts": total_artifacts,
            "objects": total_objects,
            "edges": total_edges,
            "kinds": kinds,
            "domains": domains,
            "edge_types": edge_types,
        }


# Install optional payment middleware only after all routes are declared.
from feedify.x402 import install_x402
install_x402(app)
