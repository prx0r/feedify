#!/usr/bin/env python3
"""
Reality Feed Full Test - 10 Logged Runs
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from feedify.reality.registry import RealityRegistry


def run_test(run_id: int):
    """Run one test pass"""
    print(f"\n{'='*60}")
    print(f"RUN {run_id}/10 - {datetime.now().isoformat()}")
    print(f"{'='*60}")
    
    registry = RealityRegistry()
    events = registry.scan_all()
    stats = registry.get_stats()
    
    print(f"\n--- Run {run_id} Results ---")
    print(f"Events: {len(events)}")
    print(f"By source: {stats['by_source']}")
    print(f"By type: {stats['by_type']}")
    
    # Log to file
    log_entry = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "events": len(events),
        "stats": stats,
    }
    
    with open("data/reality_test_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    return len(events)


def main():
    print("=" * 60)
    print("REALITY FEED - 10 LOGGED TEST RUNS")
    print(f"Start: {datetime.now().isoformat()}")
    print("=" * 60)
    
    total_events = 0
    for i in range(1, 11):
        count = run_test(i)
        total_events += count
    
    print(f"\n{'='*60}")
    print(f"COMPLETE - Total events across 10 runs: {total_events}")
    print(f"End: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
