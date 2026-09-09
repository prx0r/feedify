"""Signal-to-stock-movement mapper — tracks which signals predict moves."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SignalMapper:
    """Maps signals to stock movements for backtesting."""

    def __init__(self):
        self.mappings: list[dict[str, Any]] = []

    def add_mapping(self, signal_id: str, ticker: str, signal_score: float,
                    signal_type: str, days_before: int, days_after: int,
                    return_pct: float, is_correct: bool):
        """Add a signal-to-movement mapping."""
        self.mappings.append({
            "signal_id": signal_id,
            "ticker": ticker,
            "signal_score": signal_score,
            "signal_type": signal_type,
            "days_before": days_before,
            "days_after": days_after,
            "return_pct": return_pct,
            "is_correct": is_correct,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_accuracy(self) -> float:
        """Calculate overall accuracy."""
        if not self.mappings:
            return 0.0
        correct = sum(1 for m in self.mappings if m["is_correct"])
        return correct / len(self.mappings)

    def get_avg_return(self) -> float:
        """Calculate average return for correct signals."""
        correct = [m for m in self.mappings if m["is_correct"]]
        if not correct:
            return 0.0
        return sum(m["return_pct"] for m in correct) / len(correct)

    def get_by_signal_type(self) -> dict[str, dict]:
        """Group accuracy by signal type."""
        by_type = defaultdict(list)
        for m in self.mappings:
            by_type[m["signal_type"]].append(m)
        
        result = {}
        for sig_type, mappings in by_type.items():
            correct = sum(1 for m in mappings if m["is_correct"])
            result[sig_type] = {
                "count": len(mappings),
                "accuracy": correct / len(mappings) if mappings else 0,
                "avg_return": sum(m["return_pct"] for m in mappings) / len(mappings) if mappings else 0,
            }
        return result

    def to_json(self) -> dict:
        return {"mappings": self.mappings, "summary": {
            "total": len(self.mappings),
            "accuracy": self.get_accuracy(),
            "avg_return": self.get_avg_return(),
        }}
