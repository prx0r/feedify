from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from fish.adapters import (
    AppfiguresAdapter,
    GitHubAdapter,
    GlamaAdapter,
    HackerNewsAdapter,
    StoreLeadsAdapter,
    TrustMRRAdapter,
)
from fish.models import IngestionRun, Signal, SourceRecord
from fish.schemas import NormalizedItem
from fish.settings import get_settings

from .detector import calculate_base_score, detect


ADAPTERS = {
    "trustmrr": TrustMRRAdapter,
    "glama": GlamaAdapter,
    "github": GitHubAdapter,
    "hackernews": HackerNewsAdapter,
    "storeleads": StoreLeadsAdapter,
    "appfigures": AppfiguresAdapter,
}


def upsert_item(session: Session, item: NormalizedItem) -> tuple[SourceRecord, bool]:
    existing = session.scalar(
        select(SourceRecord).where(
            SourceRecord.source_type == item.source_type,
            SourceRecord.external_id == item.external_id,
        )
    )
    created = existing is None
    record = existing or SourceRecord(source_type=item.source_type, external_id=item.external_id, title=item.title)
    record.title = item.title
    record.url = item.url
    record.body = item.body
    record.author = item.author
    record.published_at = item.published_at
    record.observed_at = datetime.now(timezone.utc)
    record.metrics = item.metrics
    record.raw = item.raw
    if created:
        session.add(record)
        session.flush()
    return record, created


def ensure_signals(session: Session, record: SourceRecord, item: NormalizedItem) -> int:
    count = 0
    for draft in detect(item):
        existing = session.scalar(
            select(Signal).where(Signal.record_id == record.id, Signal.signal_type == draft.signal_type)
        )
        if existing:
            # Refresh the score inputs as upstream economic data changes.
            signal = existing
        else:
            signal = Signal(record_id=record.id, signal_type=draft.signal_type, title=draft.title, summary=draft.summary)
            session.add(signal)
            count += 1
        signal.domain = draft.domain
        signal.title = draft.title
        signal.summary = draft.summary
        signal.why_it_matters = draft.why_it_matters
        signal.novelty = draft.novelty
        signal.actionability = draft.actionability
        signal.source_proximity = draft.source_proximity
        signal.confidence = draft.confidence
        signal.evidence_strength = draft.evidence_strength
        signal.base_score = calculate_base_score(draft)
        signal.tags = draft.tags
        signal.metadata_json = draft.metadata
    return count


async def ingest_source(session: Session, source_name: str, limit: int | None = None) -> IngestionRun:
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
        signals_created = 0
        for item in items:
            record, created = upsert_item(session, item)
            inserted += int(created)
            signals_created += ensure_signals(session, record, item)
        run.status = "ok"
        run.fetched = len(items)
        run.inserted = inserted
        run.signals_created = signals_created
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


async def ingest_all(session: Session, sources: Iterable[str] | None = None, limit: int | None = None) -> list[IngestionRun]:
    names = list(sources or ADAPTERS.keys())
    runs: list[IngestionRun] = []
    for name in names:
        if name not in ADAPTERS:
            continue
        runs.append(await ingest_source(session, name, limit))
    return runs
