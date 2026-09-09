"""ML Analysis of the Acceleration Thesis Graph.

Based on arxiv research:
- TRACE: Temporal knowledge graph + LLM for stock prediction
- GAPNet: Graph adaptation for stock ranking
- FinInvest-GTCN: Graph-temporal-causal network
- Semiconductor supply chain: LLM-based risk extraction

Key insight: Knowledge graphs + LLMs work well for financial prediction.
The graph captures relational dynamics that price alone misses.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_graph() -> dict[str, Any]:
    """Load the knowledge graph."""
    graph_path = Path(__file__).parent.parent.parent / "specs" / "knowledge_graph.json"
    if graph_path.exists():
        return json.loads(graph_path.read_text())
    return {"nodes": [], "edges": []}


def load_stocks() -> dict[str, Any]:
    """Load all stock analyses."""
    stocks = {}
    for f in Path(__file__).parent.parent.parent / "specs" / "stocks" / "*":
        analysis_path = f / "analysis.json"
        if analysis_path.exists():
            stocks[f.name] = json.loads(analysis_path.read_text())
    return stocks


def compute_graph_metrics(graph: dict) -> dict[str, Any]:
    """Compute basic graph metrics."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Count by type
    node_types = {}
    for n in nodes:
        t = n.get("type", "unknown")
        node_types[t] = node_types.get(t, 0) + 1

    # Count by relation
    edge_rels = {}
    for e in edges:
        r = e.get("relation", "unknown")
        edge_rels[r] = edge_rels.get(r, 0) + 1

    # Find most connected nodes
    connections = {}
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        connections[src] = connections.get(src, 0) + 1
        connections[tgt] = connections.get(tgt, 0) + 1

    top_connected = sorted(connections.items(), key=lambda x: -x[1])[:10]

    return {
        "node_types": node_types,
        "edge_relations": edge_rels,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "top_connected": top_connected,
    }


def compute_thesis_alignment(stocks: dict) -> dict[str, Any]:
    """Compute thesis alignment across all stocks."""
    alignments = []
    for ticker, stock in stocks.items():
        thesis_score = stock.get("thesis_score", 0)
        cap = stock.get("financials", {}).get("market_cap_b", 0)
        pe = stock.get("financials", {}).get("pe", 0)
        rev_growth = stock.get("financials", {}).get("rev_growth_pct", 0)

        # Alignment score
        alignment = thesis_score * 10
        if pe and pe > 0:
            if pe < 20: alignment += 10
            elif pe < 30: alignment += 5
        if rev_growth and rev_growth > 30:
            alignment += 10
        alignment = max(0, min(100, alignment))

        alignments.append({
            "ticker": ticker,
            "thesis_score": thesis_score,
            "alignment": alignment,
            "cap": cap,
            "pe": pe,
            "rev_growth": rev_growth,
        })

    alignments.sort(key=lambda x: -x["alignment"])

    return {
        "total_stocks": len(alignments),
        "avg_alignment": sum(a["alignment"] for a in alignments) / len(alignments) if alignments else 0,
        "top_aligned": alignments[:5],
        "bottom_aligned": alignments[-5:],
    }


def generate_backtest_signals(stocks: dict, graph: dict) -> list[dict[str, Any]]:
    """Generate backtest signals from stocks and graph."""
    signals = []

    for ticker, stock in stocks.items():
        thesis_score = stock.get("thesis_score", 0)
        cap = stock.get("financials", {}).get("market_cap_b", 0)
        pe = stock.get("financials", {}).get("pe", 0)
        rev_growth = stock.get("financials", {}).get("rev_growth_pct", 0)
        bottleneck = stock.get("bottleneck", "")

        # Signal strength
        strength = thesis_score * 10

        # Convexity (small cap + high thesis)
        if cap < 0.5:
            convexity = "EXTREME"
        elif cap < 2:
            convexity = "HIGH"
        elif cap < 10:
            convexity = "MODERATE"
        else:
            convexity = "LOW"

        # Buy signal
        if strength > 80 and convexity in ("EXTREME", "HIGH"):
            signal = "STRONG_BUY"
        elif strength > 70:
            signal = "BUY"
        elif strength > 60:
            signal = "WATCH"
        else:
            signal = "HOLD"

        signals.append({
            "ticker": ticker,
            "signal": signal,
            "strength": strength,
            "convexity": convexity,
            "thesis_score": thesis_score,
            "bottleneck": bottleneck,
            "cap": cap,
            "pe": pe,
            "rev_growth": rev_growth,
        })

    signals.sort(key=lambda x: -x["strength"])
    return signals


def run_analysis() -> dict[str, Any]:
    """Run full ML analysis."""
    graph = load_graph()
    stocks = load_stocks()

    graph_metrics = compute_graph_metrics(graph)
    thesis_alignment = compute_thesis_alignment(stocks)
    backtest_signals = generate_backtest_signals(stocks, graph)

    return {
        "graph": graph_metrics,
        "thesis_alignment": thesis_alignment,
        "backtest_signals": backtest_signals,
        "summary": {
            "total_nodes": graph_metrics["total_nodes"],
            "total_edges": graph_metrics["total_edges"],
            "total_stocks": thesis_alignment["total_stocks"],
            "avg_alignment": thesis_alignment["avg_alignment"],
            "strong_buys": len([s for s in backtest_signals if s["signal"] == "STRONG_BUY"]),
            "buys": len([s for s in backtest_signals if s["signal"] == "BUY"]),
            "watches": len([s for s in backtest_signals if s["signal"] == "WATCH"]),
        },
    }
