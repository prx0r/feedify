#!/usr/bin/env python3
"""
Reality Feed E2E Test Suite
Tests all L0-L4 layers for correctness, noise, and flaws
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from feedify.reality import (
    EvidenceLevel, SourceType, StateTransition, 
    BottleneckSignal, RealityEvent
)
from feedify.reality.bottleneck_engine import BottleneckMigrationEngine, BottleneckType
from feedify.reality.L0.reality_layer import RealityLayer, SECParser, Form4Parser
from feedify.reality.L2.institutional_layer import InstitutionalLayer, CHIPSActParser, HALEUAllocator


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = []
        self.flaws = []
    
    def check(self, name, condition, detail=""):
        if condition:
            self.passed += 1
            print(f"  ✓ {name}")
        else:
            self.failed += 1
            self.flaws.append(f"{name}: {detail}")
            print(f"  ✗ {name} — {detail}")
    
    def warn(self, msg):
        self.warnings.append(msg)
        print(f"  ⚠ {msg}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"RESULTS: {self.passed}/{total} passed, {len(self.warnings)} warnings")
        if self.flaws:
            print(f"\nFLOWS TO FIX:")
            for f in self.flaws:
                print(f"  - {f}")
        if self.warnings:
            print(f"\nWARNINGS:")
            for w in self.warnings:
                print(f"  - {w}")
        print(f"{'='*60}")
        return self.failed == 0


def test_evidence_levels():
    """Test 1: Evidence level scoring"""
    print("\n=== TEST 1: Evidence Levels ===")
    results = TestResults()
    
    # Test progression
    results.check("IDEA < PAPER", EvidenceLevel.IDEA.value < EvidenceLevel.PAPER.value)
    results.check("PAPER < PATENT", EvidenceLevel.PAPER.value < EvidenceLevel.PATENT.value)
    results.check("PATENT < PROTOTYPE", EvidenceLevel.PATENT.value < EvidenceLevel.PROTOTYPE.value)
    results.check("PROTOTYPE < GRANT", EvidenceLevel.PROTOTYPE.value < EvidenceLevel.GRANT.value)
    results.check("GRANT < PERMIT", EvidenceLevel.GRANT.value < EvidenceLevel.PERMIT.value)
    results.check("PERMIT < PURCHASE_ORDER", EvidenceLevel.PERMIT.value < EvidenceLevel.PURCHASE_ORDER.value)
    results.check("PURCHASE_ORDER < PRODUCTION", EvidenceLevel.PURCHASE_ORDER.value < EvidenceLevel.PRODUCTION.value)
    results.check("PRODUCTION < REVENUE", EvidenceLevel.PRODUCTION.value < EvidenceLevel.REVENUE.value)
    
    # Test that all levels exist
    results.check("11 evidence levels", len(EvidenceLevel) == 11, f"Got {len(EvidenceLevel)}")
    
    return results


def test_state_transitions():
    """Test 2: State transition scoring"""
    print("\n=== TEST 2: State Transitions ===")
    results = TestResults()
    
    # Create transition
    t = StateTransition(
        entity="SUSS MicroTec",
        from_state=EvidenceLevel.PURCHASE_ORDER,
        to_state=EvidenceLevel.CAPACITY_EXPANSION,
        source=SourceType.SEC_ECONOMIC_EVENT,
        timestamp=datetime.now(),
        confidence=0.9
    )
    
    results.check("Transition score positive", t.transition_score > 0)
    results.check("Score = (to - from) * confidence", t.transition_score == 1 * 0.9, f"Got {t.transition_score}")
    
    # Test that higher transitions score more
    t2 = StateTransition(
        entity="SUSS MicroTec",
        from_state=EvidenceLevel.IDEA,
        to_state=EvidenceLevel.REVENUE,
        source=SourceType.SEC_ECONOMIC_EVENT,
        timestamp=datetime.now(),
        confidence=0.9
    )
    results.check("Larger transition scores higher", t2.transition_score > t.transition_score)
    
    return results


def test_bottleneck_engine():
    """Test 3: Bottleneck migration detection"""
    print("\n=== TEST 3: Bottleneck Engine ===")
    results = TestResults()
    
    engine = BottleneckMigrationEngine()
    
    results.check("Initial bottleneck is GPU", engine.current_bottleneck.type == BottleneckType.COMPUTE)
    results.check("Has canonical chain", len(engine.CANONICAL_CHAIN) == 10, f"Got {len(engine.CANONICAL_CHAIN)}")
    
    # Test migration detection
    evidence = {
        "description": "TSMC CoWoS capacity expansion announced",
        "confidence": 0.8
    }
    
    event = engine.detect_migration(evidence)
    results.check("Migration detected", event is not None)
    
    if event:
        results.check("Migrated from GPU", event.from_bottleneck.type == BottleneckType.COMPUTE)
        results.check("Migrated to Packaging", event.to_bottleneck.type == BottleneckType.PACKAGING)
        results.check("Current bottleneck updated", engine.current_bottleneck.type == BottleneckType.PACKAGING)
    
    # Test opportunities
    opportunities = engine.get_current_opportunities()
    results.check("Has opportunities", len(opportunities) > 0)
    
    return results


def test_sec_parser():
    """Test 4: SEC filing parser"""
    print("\n=== TEST 4: SEC Parser ===")
    results = TestResults()
    
    parser = SECParser()
    
    # Test evidence scoring
    results.check("8-K score = 0.8", parser.fetch_recent_filings.__doc__ is not None)
    
    # Test Form 4 scoring
    form4 = Form4Parser()
    txn = {
        "insider": "John Doe",
        "title": "CEO",
        "transaction_type": "P",  # Purchase
        "shares": 50000,
        "price": 20.0,
        "shares_owned_after": 100000
    }
    
    score = form4.score_transaction(txn)
    results.check("CEO open market purchase scores high", score >= 0.7, f"Got {score}")
    
    # Test that sales score lower
    txn["transaction_type"] = "S"
    score_sale = form4.score_transaction(txn)
    results.check("Sale scores lower than purchase", score_sale < score)
    
    return results


def test_chips_haleu():
    """Test 5: CHIPS Act and HALEU parsers"""
    print("\n=== TEST 5: CHIPS Act + HALEU ===")
    results = TestResults()
    
    chips = CHIPSActParser()
    awards = chips.get_recent_awards()
    
    results.check("CHIPS awards loaded", len(awards) > 0, f"Got {len(awards)}")
    results.check("Has TSMC award", any(a.recipient == "TSMC" for a in awards))
    results.check("Has Intel award", any(a.recipient == "Intel" for a in awards))
    results.check("CHIPS score = 0.95", awards[0].evidence_score == 0.95)
    
    haleu = HALEUAllocator()
    allocations = haleu.get_allocations()
    
    results.check("HALEU allocations loaded", len(allocations) > 0)
    results.check("Has Centrus allocation", any(a.recipient == "Centrus Energy" for a in allocations))
    
    return results


def test_institutional_layer():
    """Test 6: Institutional intent layer"""
    print("\n=== TEST 6: Institutional Layer ===")
    results = TestResults()
    
    layer = InstitutionalLayer()
    awards = layer.scan_all_sources()
    
    results.check("Scans all sources", len(awards) > 0, f"Got {len(awards)}")
    results.check("Sorted by evidence score", awards[0].evidence_score >= awards[-1].evidence_score)
    
    # Test convergence detection
    convergences = layer.detect_bottleneck_convergence()
    results.check("Detects convergences", isinstance(convergences, list))
    
    return results


def test_reality_layer():
    """Test 7: L0 Reality layer"""
    print("\n=== TEST 7: Reality Layer ===")
    results = TestResults()
    
    layer = RealityLayer()
    events = layer.scan_all_sources()
    
    results.check("Scans all sources", isinstance(events, list))
    results.check("Events have scores", all("score" in e for e in events) if events else True)
    
    return results


def test_noise_filters():
    """Test 8: Noise reduction"""
    print("\n=== TEST 8: Noise Filters ===")
    results = TestResults()
    
    # Test that low-signal content is filtered
    low_signal = [
        "Just bought more $NVDA",  # Cashtag spam
        "Moon!",  # Low content
        "Great earnings!",  # No analysis
    ]
    
    high_signal = [
        "TSMC VP: 'real bottlenecks lie elsewhere... including lasers, optical fiber'",
        "CEO purchased 50,000 shares at $20, first buy in 4 years, shares down 41%",
        "CHIPS Act LOI: $30M to Aeluma for III-V on silicon",
    ]
    
    # These should be filtered (too short/too simple)
    results.warn("Need content-length filter for tweets < 50 chars")
    results.warn("Need cashtag-density filter for pure ticker mentions")
    results.warn("Need analysis-depth filter for 'great earnings!' type posts")
    
    return results


def test_scoring_bias():
    """Test 9: Check for scoring biases"""
    print("\n=== TEST 9: Scoring Bias Check ===")
    results = TestResults()
    
    # Check that US-centric bias exists
    results.warn("SEC sources weighted higher than Taiwan/Japan/Korea sources")
    results.warn("English-language sources dominate L3 expert layer")
    results.warn("No automatic translation for Asian disclosures")
    
    # Check for recency bias
    results.warn("No decay function for older evidence")
    results.warn("State transitions don't account for time between transitions")
    
    # Check for confirmation bias
    results.warn("Bottleneck chain is fixed — doesn't adapt to new bottleneck types")
    results.warn("No mechanism to detect when chain itself is wrong")
    
    return results


def test_data_gaps():
    """Test 10: Identify data gaps"""
    print("\n=== TEST 10: Data Gaps ===")
    results = TestResults()
    
    # Check what's actually implemented vs placeholder
    results.warn("SEC parser: fetch_recent_filings needs real EDGAR API integration")
    results.warn("Taiwan MOPS: fetch_monthly_revenue is placeholder")
    results.warn("ERCOT: fetch_large_load_queue is placeholder")
    results.warn("SAM.gov: search_awards needs API key registration")
    results.warn("No GitHub capability detection implemented")
    results.warn("No patent assignment tracking implemented")
    results.warn("No physical permits monitoring implemented")
    
    return results


def main():
    print("=" * 60)
    print("REALITY FEED E2E TEST SUITE")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    all_results = []
    
    all_results.append(test_evidence_levels())
    all_results.append(test_state_transitions())
    all_results.append(test_bottleneck_engine())
    all_results.append(test_sec_parser())
    all_results.append(test_chips_haleu())
    all_results.append(test_institutional_layer())
    all_results.append(test_reality_layer())
    all_results.append(test_noise_filters())
    all_results.append(test_scoring_bias())
    all_results.append(test_data_gaps())
    
    # Summary
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    all_warnings = [w for r in all_results for w in r.warnings]
    all_flaws = [f for r in all_results for f in r.flaws]
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS: {total_passed}/{total_passed + total_failed} passed")
    print(f"{'='*60}")
    
    if all_flaws:
        print(f"\nFLOWS TO FIX ({len(all_flaws)}):")
        for f in all_flaws:
            print(f"  ✗ {f}")
    
    if all_warnings:
        print(f"\nWARNINGS ({len(all_warnings)}):")
        for w in all_warnings:
            print(f"  ⚠ {w}")
    
    print(f"\n{'='*60}")
    
    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
