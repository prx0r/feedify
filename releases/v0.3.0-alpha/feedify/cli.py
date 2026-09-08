from __future__ import annotations

import argparse
import asyncio

from feedify.db import SessionLocal, init_db
from feedify.seed import seed
from feedify.services.ingestion import ADAPTERS, ingest_all


async def _ingest(names: list[str] | None, limit: int | None) -> None:
    init_db()
    with SessionLocal() as session:
        runs = await ingest_all(session, names, limit)
        for run in runs:
            print(
                f"{run.source_type:12} {run.status:22} fetched={run.fetched:<3} "
                f"inserted={run.inserted:<3} signals={run.signals_created:<3} {run.error or ''}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(prog="feedify")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("sources", nargs="*", choices=sorted(ADAPTERS.keys()))
    ingest.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if args.command == "seed":
        seed()
        print("Seeded Feedify.")
    elif args.command == "ingest":
        asyncio.run(_ingest(args.sources or None, args.limit))


if __name__ == "__main__":
    main()
