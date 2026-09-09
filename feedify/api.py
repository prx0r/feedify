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
from feedify.models import Feed, IngestionRun, Signal, SourceRecord
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
    signal_type: str | None = None,
    lab: str | None = None,
) -> list[dict[str, Any]]:
    """Quantum × AGI frontier signals with scoring."""
    from feedify.services.quantum_agi_scoring import score_quantum_agi_signal, PRIORITY_WEIGHTS

    with SessionLocal() as session:
        # Load the frontier watchlist
        import json
        from pathlib import Path
        watchlist_path = Path(__file__).parent.parent / "config" / "acceleration_watchlist.json"
        watchlist = []
        if watchlist_path.exists():
            watchlist = json.loads(watchlist_path.read_text())

        # Build account lookup
        account_map = {}
        for entry in watchlist:
            account_map[entry["handle"].lower()] = entry

        # Get X signals from frontier accounts
        stmt = (
            select(Signal)
            .options(joinedload(Signal.record))
            .join(SourceRecord)
            .where(SourceRecord.source_type == "x")
            .order_by(Signal.created_at.desc())
            .limit(limit * 3)  # Get more to filter
        )
        rows = session.scalars(stmt).all()

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
        stmt = select(Signal).options(joinedload(Signal.record)).order_by(Signal.created_at.desc()).limit(50)
        rows = session.scalars(stmt).all()
        for s in rows:
            if s.record:
                recent.append({
                    "id": str(s.id),
                    "title": s.title,
                    "source": s.record.source_type,
                    "author": s.record.author,
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
    signal_type: str | None = None,
) -> list[dict[str, Any]]:
    """Insider signals with transaction-based scoring."""
    with SessionLocal() as session:
        # First get verified insider signals (OpenInsider, SEC EDGAR)
        verified_stmt = (
            select(Signal)
            .options(joinedload(Signal.record))
            .where(
                Signal.signal_type.contains("OPENINSIDER_")
                | Signal.signal_type.contains("SEC_4_")
                | Signal.tags.contains("openinsider")
                | Signal.tags.contains("sec-form4")
            )
            .order_by(Signal.base_score.desc())
        )
        
        verified_rows = session.scalars(verified_stmt.limit(limit)).all()
        
        # Then get X discovery signals with insider keywords
        x_stmt = (
            select(Signal)
            .options(joinedload(Signal.record))
            .join(SourceRecord)
            .where(SourceRecord.source_type == "x")
            .order_by(Signal.base_score.desc())
        )
        
        x_rows = session.scalars(x_stmt.limit(limit)).all()
        
        # Combine: verified first, then X discovery
        all_rows = list(verified_rows) + list(x_rows)

        # Filter to insider-relevant signals
        insider_keywords = [
            'insider', 'form 4', 'purchased', 'bought', 'sold', 'trade',
            'disclosure', 'congress', 'senate', 'representative', 'filing',
            'acquisition', 'stake', 'position', 'buy', 'sell',
        ]

        results = []
        seen_ids = set()
        
        for s in all_rows:
            if s.id in seen_ids:
                continue
            seen_ids.add(s.id)
            
            meta = s.metadata_json or {}
            m = s.record.metrics if s.record else {}
            tags = [t.lower() for t in (s.tags or [])]
            title_lower = (s.title or "").lower()
            summary_lower = (s.summary or "").lower()

            # Check if this is an insider signal
            is_verified_insider = (
                s.signal_type.startswith("SEC_")
                or s.signal_type.startswith("OPENINSIDER_")
                or m.get("filing_type") == "4"
                or m.get("reporting_owner")
                or "openinsider" in tags
                or "sec-form4" in tags
            )
            
            is_x_insider = (
                s.record
                and s.record.source_type == "x"
                and any(kw in title_lower or kw in summary_lower for kw in insider_keywords)
            )

            if not is_verified_insider and not is_x_insider:
                continue

            # Extract insider-specific data
            ticker = m.get("issuer_ticker", "")
            owner = m.get("reporting_owner", "")
            txn_code = m.get("transaction_code", "")
            total_value = m.get("total_value", 0)
            is_10b5 = m.get("is_10b5_1", False)
            insider_score = meta.get("insider_score", int(s.base_score * 100))
            insider_tier = meta.get("tier", "C")
            breakdown = meta.get("score_breakdown", {})
            sec_url = m.get("sec_url", "")

            # Detect frontier stocks from ticker or tags
            from feedify.services.insider_scoring import is_frontier, get_frontier_sector, ALL_FRONTIER
            if not ticker:
                # Try to extract ticker from tags or title
                for tag in tags:
                    if tag.upper() in ALL_FRONTIER:
                        ticker = tag.upper()
                        break
            is_frontier_stock = is_frontier(ticker) if ticker else False
            frontier_sector = get_frontier_sector(ticker) if ticker else None

            # Transaction code labels
            code_labels = {
                "P": "Open-Market Purchase",
                "S": "Open-Market Sale",
                "A": "Stock Award",
                "M": "Option Exercise",
                "F": "Tax Withholding",
                "G": "Gift",
            }
            txn_label = code_labels.get(txn_code, "")

            # Determine signal interpretation
            if is_verified_insider:
                if txn_code == "P" or "purchase" in title_lower:
                    interpretation = (
                        "🟢 PURCHASE — Insider bought shares on the open market. "
                        "This is a positive signal when the amount is significant and not 10b5-1 pre-planned."
                    )
                elif txn_code == "S" or "sale" in title_lower:
                    interpretation = (
                        "🔴 SALE — Insider sold shares. "
                        "Many sales are routine (tax, diversification), but large discretionary sales warrant attention."
                    )
                else:
                    interpretation = (
                        "📋 VERIFIED FILING — Confirmed insider transaction from SEC EDGAR/OpenInsider. "
                        "Review transaction code and context for significance."
                    )
            else:
                # X discovery signal
                if "congress" in tags or "senate" in title_lower:
                    interpretation = (
                        "🏛️ CONGRESSIONAL — Member of Congress disclosed a trade. "
                        "These can be delayed up to 45 days. Check committee relevance and trade size."
                    )
                else:
                    interpretation = (
                        "🔍 X DISCOVERY — Insider activity spotted on X. "
                        "This is unverified; check SEC filings for confirmation."
                    )

            results.append({
                "id": s.id,
                "ticker": ticker,
                "owner": owner,
                "txn_code": txn_code,
                "txn_label": txn_label or ("Purchase" if txn_code == "P" else "Sale" if txn_code == "S" else "Filing"),
                "total_value": total_value,
                "is_10b5": is_10b5,
                "score": insider_score,
                "tier": insider_tier,
                "is_frontier": is_frontier_stock,
                "frontier_sector": frontier_sector,
                "interpretation": interpretation,
                "title": s.title,
                "summary": s.summary,
                "domain": s.domain,
                "tags": s.tags,
                "source": s.record.source_type if s.record else "unknown",
                "author": s.record.author if s.record else "unknown",
                "url": sec_url or (s.record.url if s.record else None),
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "breakdown": breakdown,
                "is_verified": is_verified_insider,
            })

            if len(results) >= limit:
                break

        # Apply sector filter in Python (after frontier detection)
        if sector:
            sector_upper = sector.upper()
            sector_map = {"AI": "AI", "CHIPS": "CHIPS", "QUANTUM": "QUANTUM", "POWER": "POWER_INFRA"}
            target_sector = sector_map.get(sector_upper, sector_upper)
            results = [r for r in results if r.get("frontier_sector") == target_sector]

        return results


@app.get("/api/insiders/stats")
def insiders_stats() -> dict[str, Any]:
    """Insider intelligence statistics."""
    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(Signal)) or 0

        # Count by domain
        domains = {}
        for row in session.scalars(select(Signal.domain, func.count()).group_by(Signal.domain)).all():
            domains[row[0]] = row[1]

        # Count by signal type
        signal_types = {}
        for row in session.scalars(
            select(Signal.signal_type, func.count())
            .where(Signal.signal_type.contains("SEC_") | Signal.signal_type.contains("OPENINSIDER_"))
            .group_by(Signal.signal_type)
        ).all():
            signal_types[row[0]] = row[1]

        # Top tickers from metadata
        tickers: dict[str, int] = {}
        for s in session.scalars(select(Signal).limit(500)).all():
            if s.metadata_json:
                ticker = s.metadata_json.get("issuer_ticker") or s.record.metrics.get("issuer_ticker", "") if s.record else ""
                if ticker:
                    tickers[ticker] = tickers.get(ticker, 0) + 1

        return {
            "total_signals": total,
            "domains": domains,
            "insider_signal_types": signal_types,
            "top_tickers": dict(sorted(tickers.items(), key=lambda x: -x[1])[:20]),
        }


# ── AI Insider Analysis ──────────────────────────────────────────────────────

@app.get("/api/insiders/summary")
async def insiders_summary() -> dict[str, Any]:
    """AI-generated summary of highest alpha insider signals."""
    from feedify.services.ai_insiders import summarize_insiders

    # Get insider signals
    with SessionLocal() as session:
        stmt = (
            select(Signal)
            .options(joinedload(Signal.record))
            .join(SourceRecord)
            .order_by(Signal.base_score.desc())
            .limit(50)
        )
        rows = session.scalars(stmt).all()

        # Filter to insider-relevant
        insider_keywords = ['insider', 'form 4', 'purchased', 'bought', 'sold', 'trade', 'congress']
        signals = []
        for s in rows:
            meta = s.metadata_json or {}
            m = s.record.metrics if s.record else {}
            tags = [t.lower() for t in (s.tags or [])]
            title_lower = (s.title or "").lower()
            summary_lower = (s.summary or "").lower()

            is_insider = (
                s.signal_type.startswith("SEC_")
                or s.signal_type.startswith("OPENINSIDER_")
                or m.get("filing_type") == "4"
                or "openinsider" in tags
                or "sec-form4" in tags
                or s.record.source_type == "x"
                and any(kw in title_lower or kw in summary_lower for kw in insider_keywords)
            )
            if not is_insider:
                continue

            signals.append({
                "ticker": m.get("issuer_ticker", ""),
                "owner": m.get("reporting_owner", ""),
                "score": meta.get("insider_score", int(s.base_score * 100)),
                "tier": meta.get("tier", "C"),
                "txn_label": m.get("transaction_label", ""),
                "total_value": m.get("total_value", 0),
                "is_verified": s.signal_type.startswith("OPENINSIDER_") or s.signal_type.startswith("SEC_"),
                "is_frontier": meta.get("is_frontier", False),
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "interpretation": s.why_it_matters or "",
            })

    settings = get_settings()
    api_key = settings.llm_api_key or "sk-A5QHR5MRtUNec7BWqiRsZ0GAYck0CRT2Movsk7Q6U3UwcV77Y6G3TMXOhhyKh855"

    summary = await summarize_insiders(signals, api_key)
    return {"summary": summary, "signal_count": len(signals)}


@app.post("/api/insiders/chat")
async def insiders_chat(payload: dict[str, Any]) -> dict[str, str]:
    """Chat about insider signals with AI."""
    from feedify.services.ai_insiders import chat_with_insiders

    message = payload.get("message", "")
    history = payload.get("history", [])

    if not message:
        raise HTTPException(400, "message is required")

    # Get insider signals
    with SessionLocal() as session:
        stmt = (
            select(Signal)
            .options(joinedload(Signal.record))
            .join(SourceRecord)
            .order_by(Signal.base_score.desc())
            .limit(50)
        )
        rows = session.scalars(stmt).all()

        insider_keywords = ['insider', 'form 4', 'purchased', 'bought', 'sold', 'trade', 'congress']
        signals = []
        for s in rows:
            m = s.record.metrics if s.record else {}
            tags = [t.lower() for t in (s.tags or [])]
            title_lower = (s.title or "").lower()
            summary_lower = (s.summary or "").lower()

            is_insider = (
                s.signal_type.startswith("SEC_")
                or s.signal_type.startswith("OPENINSIDER_")
                or m.get("filing_type") == "4"
                or "openinsider" in tags
                or "sec-form4" in tags
                or s.record.source_type == "x"
                and any(kw in title_lower or kw in summary_lower for kw in insider_keywords)
            )
            if not is_insider:
                continue

            meta = s.metadata_json or {}
            signals.append({
                "ticker": m.get("issuer_ticker", ""),
                "owner": m.get("reporting_owner", ""),
                "score": meta.get("insider_score", int(s.base_score * 100)),
                "tier": meta.get("tier", "C"),
                "txn_label": m.get("transaction_label", ""),
                "total_value": m.get("total_value", 0),
                "is_verified": s.signal_type.startswith("OPENINSIDER_") or s.signal_type.startswith("SEC_"),
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "interpretation": s.why_it_matters or "",
            })

    settings = get_settings()
    api_key = settings.llm_api_key or ""

    response = await chat_with_insiders(message, signals, api_key, history)
    return {"response": response}


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

        # Get recent signals
        signals_stmt = (
            select(Signal)
            .options(joinedload(Signal.record))
            .order_by(Signal.created_at.desc())
            .limit(100)
        )
        signals = session.scalars(signals_stmt).all()

        # Get feeds
        feeds = session.scalars(select(Feed)).all()

        # Get source status
        sources = session.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(20)).all()

        # Build context
        signal_data = []
        for s in signals:
            m = s.record.metrics if s.record else {}
            signal_data.append({
                "title": s.title,
                "summary": s.summary[:200] if s.summary else "",
                "domain": s.domain,
                "score": s.base_score,
                "type": s.signal_type,
                "tags": s.tags,
                "ticker": m.get("issuer_ticker", ""),
                "owner": m.get("reporting_owner", ""),
                "source": s.record.source_type if s.record else "unknown",
                "author": s.record.author if s.record else "unknown",
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })

        feed_data = [{"name": f.name, "slug": f.slug, "prompt": f.prompt[:100]} for f in feeds]
        source_data = [{"type": s.source_type, "status": s.status, "fetched": s.fetched} for s in sources]

    # Build prompt
    context_str = json.dumps(signal_data[:30], indent=2)
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


# Install optional payment middleware only after all routes are declared.
from feedify.x402 import install_x402
install_x402(app)
