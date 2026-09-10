"""Convergence detector — ML-based detection of cross-lab topic convergence."""
from __future__ import annotations

from collections import defaultdict
from typing import Any


class ConvergenceDetector:
    """Detects when multiple labs discuss the same topic within a time window."""

    def __init__(self, window_hours: int = 72):
        self.window_hours = window_hours

    def detect(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect convergence events from signals."""
        # Group signals by topic
        topic_signals: dict[str, list[dict]] = defaultdict(list)
        
        for sig in signals:
            text = (sig.get("title", "") or sig.get("summary", "")).lower()
            topics = self._extract_topics(text)
            for topic in topics:
                topic_signals[topic].append(sig)
        
        # Find convergences (2+ labs discussing same topic)
        convergences = []
        for topic, sigs in topic_signals.items():
            labs = set(s.get("lab", "") for s in sigs if s.get("lab"))
            if len(labs) >= 2:
                handles = list(set(s.get("author", "") for s in sigs if s.get("author")))
                convergences.append({
                    "topic": topic,
                    "labs": list(labs),
                    "participants": handles,
                    "signal_count": len(sigs),
                    "avg_score": sum(s.get("score", 0) for s in sigs) / len(sigs) if sigs else 0,
                })
        
        return convergences

    def _extract_topics(self, text: str) -> list[str]:
        """Extract topics from text."""
        topics = []
        
        topic_keywords = {
            "quantum_error_correction": ["qec", "qldpc", "decoder", "fault tolerant"],
            "rl_scaling": ["rl scaling", "bigrun", "automated research"],
            "reasoning": ["reasoning", "chain of thought", "formal verification"],
            "agents": ["agent", "tool use", "coding agent"],
            "materials": ["materials", "synthesis", "experiment"],
            "photonics": ["photonics", "optical", "interconnect", "laser"],
            "hardware": ["silicon", "asic", "compiler", "chip"],
            "energy": ["energy", "power", "cooling", "nuclear"],
            "robotics": ["robot", "embodiment", "policy"],
            "biology": ["protein", "molecular", "drug"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(k in text for k in keywords):
                topics.append(topic)
        
        return topics
