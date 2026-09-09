"""Stock registry with thesis alignment and market data."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yfinance as yf


# The refined top 10 + expanded universe
STOCK_REGISTRY = [
    # Top 10 — Refined
    {
        "ticker": "SVCO",
        "company": "Silvaco",
        "category": "verification",
        "bottleneck": "AI→physics simulation",
        "thesis": "FTCO turns expensive multiphysics simulations into AI surrogate models",
        "thesis_score": 9.5,
        "weight": 16,
        "risk": "venture",
        "market_cap": "~$228M",
        "key_metric": "pipeline > market cap",
        "x_accounts": ["PhotonCap"],
    },
    {
        "ticker": "LEU",
        "company": "Centrus Energy",
        "category": "energy",
        "bottleneck": "Nuclear fuel/HALEU",
        "thesis": "Only US-owned HALEU producer, $900M DOE contract",
        "thesis_score": 9.3,
        "weight": 16,
        "risk": "physical_scarcity",
        "market_cap": "~$3.72B",
        "key_metric": "$900M DOE contract",
        "x_accounts": [],
    },
    {
        "ticker": "EROC",
        "company": "ERock",
        "category": "energy",
        "bottleneck": "On-site power generation",
        "thesis": "Utility-scale generation at datacenter site",
        "thesis_score": 9.0,
        "weight": 15,
        "risk": "execution",
        "market_cap": "~$626M",
        "key_metric": "$1.7B backlog",
        "x_accounts": ["SurmountInvest", "HyperTechInvest"],
    },
    {
        "ticker": "SDGR",
        "company": "Schrödinger",
        "category": "verification",
        "bottleneck": "Physics-based molecular verification",
        "thesis": "Bunsen agent turns physics engine into co-scientist",
        "thesis_score": 9.0,
        "weight": 12,
        "risk": "biotech",
        "market_cap": "~$1.5B",
        "key_metric": "BMS partnership",
        "x_accounts": [],
    },
    {
        "ticker": "GSIT",
        "company": "GSI Technology",
        "category": "compute",
        "bottleneck": "Compute-in-memory",
        "thesis": "Associative processing attacks data movement energy cost",
        "thesis_score": 10.0,
        "weight": 11,
        "risk": "venture",
        "market_cap": "~$216M",
        "key_metric": "Plato tapeout March 2027",
        "x_accounts": ["TheValueist"],
    },
    {
        "ticker": "MOD",
        "company": "Modine",
        "category": "cooling",
        "bottleneck": "Data center thermal management",
        "thesis": "Cooling capacity pre-sold at $4B",
        "thesis_score": 8.6,
        "weight": 9,
        "risk": "physical_scarcity",
        "market_cap": "~$10.4B",
        "key_metric": "$165M prepayment",
        "x_accounts": ["TraceyRyniec"],
    },
    {
        "ticker": "AMKR",
        "company": "Amkor Technology",
        "category": "packaging",
        "bottleneck": "Advanced packaging assembly",
        "thesis": "Nvidia $1.5B deal + 10yr TSMC partnership",
        "thesis_score": 8.5,
        "weight": 8,
        "risk": "physical_scarcity",
        "market_cap": "~$12.7B",
        "key_metric": "Nvidia+TSMC deals",
        "x_accounts": ["TheValueist"],
    },
    {
        "ticker": "RXRX",
        "company": "Recursion",
        "category": "autonomous_science",
        "bottleneck": "Proprietary experimental data",
        "thesis": "Machines interrogate biology, create proprietary observations",
        "thesis_score": 8.2,
        "weight": 6,
        "risk": "biotech",
        "market_cap": "~$1.84B",
        "key_metric": "Genentech partnership",
        "x_accounts": [],
    },
    {
        "ticker": "ALMU",
        "company": "Aeluma",
        "category": "photonics",
        "bottleneck": "InP/photonics manufacturing",
        "thesis": "Compound-semiconductor devices on scalable platforms",
        "thesis_score": 8.0,
        "weight": 5,
        "risk": "venture",
        "market_cap": "~$246M",
        "key_metric": "Tower partnership",
        "x_accounts": ["crux_capital_"],
    },
    {
        "ticker": "ONTO",
        "company": "Onto Innovation",
        "category": "verification",
        "bottleneck": "HBM/2.5D/SiPh inspection",
        "thesis": "Process control for heterogeneous packages",
        "thesis_score": 8.5,
        "weight": 6,
        "risk": "discovered",
        "market_cap": "~$13B",
        "key_metric": "$1B+ backlog",
        "x_accounts": ["HyperTechInvest"],
    },
    # Extended universe
    {
        "ticker": "SNPS",
        "company": "Synopsys",
        "category": "verification",
        "bottleneck": "Design verification software",
        "thesis": "EDA + Ansys = verification tollbooth",
        "thesis_score": 9.4,
        "weight": 0,
        "risk": "established",
        "market_cap": "~$76B",
        "key_metric": "Q3 rev $2.477B",
        "x_accounts": [],
    },
    {
        "ticker": "CRDO",
        "company": "Credo Technology",
        "category": "interconnect",
        "bottleneck": "Copper→optics transition",
        "thesis": "AEC products solve short-reach copper",
        "thesis_score": 8.9,
        "weight": 0,
        "risk": "architecture",
        "market_cap": "~$8B",
        "key_metric": "Rev $479M +114% YoY",
        "x_accounts": ["zephyr_z9"],
    },
    {
        "ticker": "FN",
        "company": "Fabrinet",
        "category": "photonics",
        "bottleneck": "Precision optical manufacturing",
        "thesis": "Sole outsourced partner for difficult optical assemblies",
        "thesis_score": 9.2,
        "weight": 0,
        "risk": "concentration",
        "market_cap": "~$14B",
        "key_metric": "Rev $4.6B +36% YoY",
        "x_accounts": ["crux_capital_"],
    },
    {
        "ticker": "VIAV",
        "company": "Viavi Solutions",
        "category": "verification",
        "bottleneck": "Optical test/measurement",
        "thesis": "Prove 1.6T/3.2T networks work",
        "thesis_score": 9.0,
        "weight": 0,
        "risk": "cyclical",
        "market_cap": "~$3B",
        "key_metric": "Rev +52.5% YoY",
        "x_accounts": ["damnang2"],
    },
    {
        "ticker": "AIXA",
        "company": "AIXTRON",
        "category": "manufacturing",
        "bottleneck": "InP laser production equipment",
        "thesis": "MOCVD systems for laser manufacturing",
        "thesis_score": 8.8,
        "weight": 0,
        "risk": "cyclical",
        "market_cap": "~€3.5B",
        "key_metric": "Orders +81% YoY",
        "x_accounts": [],
    },
    {
        "ticker": "TSEM",
        "company": "Tower Semiconductor",
        "category": "manufacturing",
        "bottleneck": "Silicon-photonics foundry capacity",
        "thesis": "$1.3B SiPh contracts signed",
        "thesis_score": 8.5,
        "weight": 0,
        "risk": "valuation",
        "market_cap": "~$4.5B",
        "key_metric": "$1.3B contracts",
        "x_accounts": [],
    },
]


def get_stock_data(tickers: list[str]) -> dict[str, Any]:
    """Fetch current market data for stocks."""
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1mo")
            
            data[ticker] = {
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("forwardPE") or info.get("trailingPE"),
                "revenue": info.get("totalRevenue"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margin": info.get("profitMargins"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "beta": info.get("beta"),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            data[ticker] = {"error": str(e)}
    
    return data


def get_thesis_alignment(stock: dict, market_data: dict) -> dict[str, Any]:
    """Compare thesis vs market reality."""
    ticker = stock["ticker"]
    data = market_data.get(ticker, {})
    
    if "error" in data:
        return {"ticker": ticker, "status": "error", "error": data["error"]}
    
    # Thesis alignment score
    thesis_score = stock["thesis_score"]
    
    # Market factors
    price = data.get("price", 0)
    pe = data.get("pe_ratio", 0)
    revenue_growth = data.get("revenue_growth", 0)
    
    # Alignment: how well does the market reflect the thesis?
    # High thesis score + low PE = undervalued relative to thesis
    # High thesis score + high PE = market agrees but priced in
    # High thesis score + negative growth = thesis not yet reflected
    
    alignment_score = thesis_score * 10  # Base from thesis
    
    if pe and pe > 0:
        if pe < 20:
            alignment_score += 10  # Cheap relative to thesis
        elif pe < 30:
            alignment_score += 5
        elif pe > 50:
            alignment_score -= 10  # Expensive
    
    if revenue_growth and revenue_growth > 0.3:
        alignment_score += 10  # Strong growth confirms thesis
    elif revenue_growth and revenue_growth < 0:
        alignment_score -= 5  # Thesis not yet reflected
    
    alignment_score = max(0, min(100, alignment_score))
    
    return {
        "ticker": ticker,
        "thesis_score": thesis_score,
        "market_price": price,
        "pe_ratio": pe,
        "revenue_growth": revenue_growth,
        "alignment_score": alignment_score,
        "thesis_aligned": alignment_score > 60,
        "thesis_divergent": alignment_score < 40,
    }


def generate_stock_report() -> dict[str, Any]:
    """Generate comprehensive stock report."""
    tickers = [s["ticker"] for s in STOCK_REGISTRY]
    market_data = get_stock_data(tickers)
    
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stocks": [],
        "summary": {},
    }
    
    aligned = 0
    divergent = 0
    
    for stock in STOCK_REGISTRY:
        alignment = get_thesis_alignment(stock, market_data.get(stock["ticker"], {}))
        report["stocks"].append({
            **stock,
            "market_data": market_data.get(stock["ticker"], {}),
            "alignment": alignment,
        })
        
        if alignment.get("thesis_aligned"):
            aligned += 1
        elif alignment.get("thesis_divergent"):
            divergent += 1
    
    report["summary"
    {
        "ticker": "6627.T",
        "company": "Tera Probe",
        "category": "verification",
        "bottleneck": "AI/HBM physical test capacity",
        "thesis": "Wafer/final testing, profits accelerating, no Western hype",
        "thesis_score": 9.0,
        "weight": 0,
        "risk": "japan_listing",
        "market_cap": "~$670M",
        "key_metric": "H1 rev +44% YoY, OP +94% YoY",
        "x_accounts": [],
    },
    {
        "ticker": "6315.T",
        "company": "TOWA",
        "category": "packaging",
        "bottleneck": "HBM4 molding/underfill",
        "thesis": "Molding/encapsulation equipment for HBM stacks",
        "thesis_score": 8.8,
        "weight": 0,
        "risk": "tech_change",
        "market_cap": "~$1.1B",
        "key_metric": "Sales +100% YoY, orders record",
        "x_accounts": [],
    },
    {
        "ticker": "ASYS",
        "company": "Amtech Systems",
        "category": "manufacturing",
        "bottleneck": "Thermal processing for advanced packaging",
        "thesis": "AI applications >40% of TPS revenue, bookings increasing",
        "thesis_score": 8.5,
        "weight": 0,
        "risk": "dilution",
        "market_cap": "~$270M",
        "key_metric": "TPS rev +25% YoY, AI >40%",
        "x_accounts": [],
    },
    {
        "ticker": "SMHN.DE",
        "company": "SUSS MicroTec",
        "category": "packaging",
        "bottleneck": "Coating/bonding for advanced packaging",
        "thesis": "Order book €473.7M, AI chip-module value chain",
        "thesis_score": 8.7,
        "weight": 0,
        "risk": "execution",
        "market_cap": "~$1.6B",
        "key_metric": "Orders €260.7M Q2, +230% YoY",
        "x_accounts": [],
    },
    {
        "ticker": "ALRIB",
        "company": "RIBER",
        "category": "photonics",
        "bottleneck": "MBE/lasers/oxide-on-silicon photonics",
        "thesis": "Epitaxy equipment for next-gen photonics + quantum",
        "thesis_score": 8.0,
        "weight": 0,
        "risk": "geopolitical",
        "market_cap": "~$210M",
        "key_metric": "ROSIE shipped to quantum player",
        "x_accounts": [],
    },
    {
        "ticker": "STDN",
        "company": "Standard Nuclear",
        "category": "energy",
        "bottleneck": "TRISO/HALEU fuel manufacturing",
        "thesis": "First US TRISO fuel manufacturer, backlog $576.9M",
        "thesis_score": 8.0,
        "weight": 0,
        "risk": "execution",
        "market_cap": "~$2B",
        "key_metric": "Backlog $576.9M",
        "x_accounts": [],
    },
    {
        "ticker": "KLIC",
        "company": "Kulicke & Soffa",
        "category": "packaging",
        "bottleneck": "Thermo-compression bonding / CPO assembly",
        "thesis": "Advanced assembly supplier for HBM/CPO/AI systems",
        "thesis_score": 7.5,
        "weight": 0,
        "risk": "established",
        "market_cap": "~$4B",
        "key_metric": "Rev $330.4M, +123% YoY",
        "x_accounts": [],
    },

] = {
        "total_stocks": len(STOCK_REGISTRY),
        "thesis_aligned": aligned,
        "thesis_divergent": divergent,
        "neutral": len(STOCK_REGISTRY) - aligned - divergent,
    }
    
    return report
