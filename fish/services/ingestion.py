from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from fish.adapters import (
    AppfiguresAdapter,
    EdgarAdapter,
    GitHubAdapter,
    GlamaAdapter,
    HackerNewsAdapter,
    OpenInsiderAdapter,
    StoreLeadsAdapter,
    TrustMRRAdapter,
    XAdapter,
)
from fish.models import Artifact, IngestionRun, Object, Edge
from fish.schemas import NormalizedItem
from fish.settings import get_settings

from .detector import compile_artifact, get_source_proximity
from .llm_compiler import llm_compile


ADAPTERS = {
    "trustmrr": TrustMRRAdapter,
    "glama": GlamaAdapter,
    "github": GitHubAdapter,
    "hackernews": HackerNewsAdapter,
    "storeleads": StoreLeadsAdapter,
    "appfigures": AppfiguresAdapter,
    "x": XAdapter,
    "sec_edgar": EdgarAdapter,
    "openinsider": OpenInsiderAdapter,
}


def upsert_artifact(session: Session, item: NormalizedItem) -> tuple[Artifact, bool]:
    existing = session.scalar(
        select(Artifact).where(
            Artifact.source_type == item.source_type,
            Artifact.external_id == item.external_id,
        )
    )
    created = existing is None
    artifact = existing or Artifact(source_type=item.source_type, external_id=item.external_id, title=item.title)
    artifact.title = item.title
    artifact.url = item.url
    artifact.body = item.body
    artifact.author = item.author
    artifact.published_at = item.published_at
    artifact.observed_at = datetime.now(timezone.utc)
    artifact.metrics = item.metrics
    artifact.raw = item.raw
    if created:
        session.add(artifact)
        session.flush()
    return artifact, created


def compile_into_graph(session: Session, artifact: Artifact, item: NormalizedItem, use_llm: bool = True) -> tuple[int, int]:
    """Run the semantic compiler on an artifact, producing Objects and Edges.
    For X posts: always try LLM first (the real intelligence), heuristic as fallback.
    For other sources: heuristic detector works fine.
    Returns (objects_created, edges_created)."""
    objects_created = 0
    edges_created = 0

    object_drafts = []
    edge_drafts = []
    score_breakdown = {}

    # For X posts: LLM compiler is PRIMARY (this is where the intelligence gap is)
    if use_llm and item.source_type == "x":
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context. We can't await here, but we CAN
                # use the heuristic detector which now has scoring built in.
                # The LLM compilation happens in the async ingest_source function.
                object_drafts, edge_drafts = compile_artifact(item, artifact.id)
            else:
                result = loop.run_until_complete(llm_compile(item))
                if len(result) == 3:
                    object_drafts, edge_drafts, score_breakdown = result
                else:
                    object_drafts, edge_drafts = result
                if not object_drafts:
                    object_drafts, edge_drafts = compile_artifact(item, artifact.id)
        except RuntimeError:
            object_drafts, edge_drafts = compile_artifact(item, artifact.id)
    elif use_llm and item.source_type in ("sec_edgar", "openinsider"):
        # SEC/OpenInsider: heuristic works well (structured data)
        object_drafts, edge_drafts = compile_artifact(item, artifact.id)
    else:
        object_drafts, edge_drafts = compile_artifact(item, artifact.id)

    for draft in object_drafts:
        existing = session.scalar(
            select(Object).where(
                Object.object_key == draft.object_key,
                Object.version == 1,
            )
        )
        if existing:
            obj = existing
        else:
            obj = Object(
                object_key=draft.object_key,
                kind=draft.kind,
                title=draft.title,
                summary=draft.summary,
                confidence=draft.confidence,
                domain=draft.domain,
                artifact_id=artifact.id,
                metadata_json=draft.metadata,
            )
            session.add(obj)
            session.flush()
            objects_created += 1

        obj.title = draft.title
        obj.summary = draft.summary
        obj.confidence = draft.confidence
        obj.domain = draft.domain
        obj.metadata_json = draft.metadata
        obj.updated_at = datetime.now(timezone.utc)

    for edge_draft in edge_drafts:
        source = session.scalar(
            select(Object).where(Object.object_key == edge_draft.source_key, Object.version == 1)
        )
        target = session.scalar(
            select(Object).where(Object.object_key == edge_draft.target_key, Object.version == 1)
        )
        if not source or not target:
            continue

        existing_edge = session.scalar(
            select(Edge).where(
                Edge.source_id == source.id,
                Edge.target_id == target.id,
                Edge.relation == edge_draft.relation,
            )
        )
        if not existing_edge:
            edge = Edge(
                source_id=source.id,
                target_id=target.id,
                relation=edge_draft.relation,
                weight=edge_draft.weight,
                evidence_artifact_id=artifact.id,
                metadata_json=edge_draft.metadata,
            )
            session.add(edge)
            edges_created += 1

    return objects_created, edges_created


async def ingest_source(session: Session, source_name: str, limit: int | None = None, use_llm: bool = True) -> IngestionRun:
    settings = get_settings()
    adapter_cls = ADAPTERS[source_name]
    run = IngestionRun(source_type=source_name)
    session.add(run)
    session.commit()
    try:
        async with adapter_cls() as adapter:
            if not adapter.configured:
                run.status = "skipped_unconfigured"
                run.finished_at = datetime.now(timezone.utc)
                session.commit()
                return run
            items = await adapter.fetch(limit or settings.feedify_ingest_limit)
        inserted = 0
        objects_created = 0
        edges_created = 0

        # For X posts: use async LLM compiler directly
        if use_llm and settings.llm_api_key and source_name == "x":
            for item in items:
                artifact, created = upsert_artifact(session, item)
                inserted += int(created)
                
                # Use LLM compiler directly (async)
                try:
                    result = await llm_compile(item)
                    if len(result) == 3:
                        obj_drafts, edge_drafts, score = result
                    else:
                        obj_drafts, edge_drafts = result
                        score = {}
                except Exception:
                    obj_drafts, edge_drafts = compile_artifact(item, artifact.id)
                    score = {}

                # Create objects
                for draft in obj_drafts:
                    existing = session.scalar(
                        select(Object).where(Object.object_key == draft.object_key, Object.version == 1)
                    )
                    if existing:
                        obj = existing
                    else:
                        obj = Object(
                            object_key=draft.object_key,
                            kind=draft.kind,
                            title=draft.title,
                            summary=draft.summary,
                            confidence=draft.confidence,
                            domain=draft.domain,
                            artifact_id=artifact.id,
                            metadata_json=draft.metadata,
                        )
                        session.add(obj)
                        session.flush()
                        objects_created += 1
                    obj.title = draft.title
                    obj.summary = draft.summary
                    obj.confidence = draft.confidence
                    obj.domain = draft.domain
                    obj.metadata_json = draft.metadata
                    obj.updated_at = datetime.now(timezone.utc)

                # Create edges
                for edge_draft in edge_drafts:
                    source = session.scalar(select(Object).where(Object.object_key == edge_draft.source_key, Object.version == 1))
                    target = session.scalar(select(Object).where(Object.object_key == edge_draft.target_key, Object.version == 1))
                    if source and target:
                        existing_edge = session.scalar(select(Edge).where(Edge.source_id == source.id, Edge.target_id == target.id, Edge.relation == edge_draft.relation))
                        if not existing_edge:
                            session.add(Edge(source_id=source.id, target_id=target.id, relation=edge_draft.relation, weight=edge_draft.weight, evidence_artifact_id=artifact.id))
                            edges_created += 1
        else:
            # Non-X sources or LLM disabled: use heuristic
            for item in items:
                artifact, created = upsert_artifact(session, item)
                inserted += int(created)
                o, e = compile_into_graph(session, artifact, item, use_llm=False)
                objects_created += o
                edges_created += e

        run.status = "ok"
        run.fetched = len(items)
        run.inserted = inserted
        run.objects_created = objects_created
        run.edges_created = edges_created
        run.finished_at = datetime.now(timezone.utc)
        session.commit()
    except Exception as exc:
        session.rollback()
        run = session.get(IngestionRun, run.id)
        if run:
            run.status = "error"
            run.error = str(exc)[:4000]
            run.finished_at = datetime.now(timezone.utc)
            session.commit()
    return run


async def ingest_all(session: Session, sources: Iterable[str] | None = None, limit: int | None = None, use_llm: bool = True) -> list[IngestionRun]:
    names = list(sources or ADAPTERS.keys())
    runs: list[IngestionRun] = []
    for name in names:
        if name not in ADAPTERS:
            continue
        runs.append(await ingest_source(session, name, limit, use_llm=use_llm))
    return runs
