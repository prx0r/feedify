"""Source reputation tracker — which X accounts produce alpha."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class SourceReputation:
    """Tracks reputation for X accounts based on signal quality."""

    def __init__(self):
        self.reputations: dict[str, dict[str, Any]] = {}

    def update(self, handle: str, signal_score: float, is_correct: bool = True):
        """Update reputation based on signal outcome."""
        if handle not in self.reputations:
            self.reputations[handle] = {
                "signals": 0,
                "correct": 0,
                "avg_score": 0,
                "total_score": 0,
            }
        
        rep = self.reputations[handle]
        rep["signals"] += 1
        if is_correct:
            rep["correct"] += 1
        rep["total_score"] += signal_score
        rep["avg_score"] = rep["total_score"] / rep["signals"]

    def get_reputation(self, handle: str) -> dict[str, Any]:
        """Get reputation for an account."""
        return self.reputations.get(handle, {
            "signals": 0,
            "correct": 0,
            "avg_score": 0,
            "total_score": 0,
        })

    def rank_accounts(self) -> list[dict[str, Any]]:
        """Rank all accounts by reputation."""
        ranked = []
        for handle, rep in self.reputations.items():
            win_rate = rep["correct"] / rep["signals"] if rep["signals"] > 0 else 0
            ranked.append({
                "handle": handle,
                "signals": rep["signals"],
                "win_rate": win_rate,
                "avg_score": rep["avg_score"],
            })
        ranked.sort(key=lambda x: x["avg_score"], reverse=True)
        return ranked

    def to_json(self) -> dict:
        return self.reputations
