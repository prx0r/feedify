"""Feedify Frontier Schema — Quantum × AGI Intelligence Graph.

BEAR tracks: Source → Event → Outcome (did the trade make money?)
Feedify tracks: Person → Post → Signal → Convergence (when does the bottleneck move?)

Key differences from BEAR:
1. People are first-class entities, not just "source handles"
2. Replies are more valuable than original posts
3. Convergence detection (multiple people discussing same thing)
4. Lab/team tracking (who works where, who collaborates)
5. Vocabulary tracking (what words people use, how they change)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SignalType(str, Enum):
    CONVERGENCE = "CONVERGENCE"          # Multiple people discussing same thing
    QUANTUM_LEAD = "QUANTUM_LEAD"        # Quantum-specific signal
    AGI_LEAD = "AGI_LEAD"                # AI/AGI-specific signal
    REGIME_CHANGE = "REGIME_CHANGE"      # Belief update language
    OBSERVATION = "OBSERVATION"          # General observation
    BELIEF_UPDATE = "BELIEF_UPDATE"      # Someone changed their mind


class PersonRole(str, Enum):
    RESEARCHER = "researcher"
    ENGINEER = "engineer"
    EXECUTIVE = "executive"
    FOUNDER = "founder"
    STUDENT = "student"
    UNKNOWN = "unknown"


class Lab(str, Enum):
    IONQ = "IonQ"
    INFLEQTION = "Infleqtion"
    IQM = "IQM"
    GOOGLE_DEEPMIND = "Google DeepMind"
    META_MSL = "Meta MSL"
    XAI = "xAI"
    ANTHROPIC = "Anthropic"
    OPENAI = "OpenAI"
    AXIOM = "Axiom"
    DEEPMIND = "DeepMind"
    UNKNOWN = "Unknown"


# ---------------------------------------------------------------------------
# Core Data Classes
# ---------------------------------------------------------------------------

@dataclass
class Person:
    """A person in the intelligence graph."""
    handle: str                          # X handle (stable ID)
    display_name: str = ""
    lab: str = ""
    role: str = ""
    priority: str = "A"                  # S++, S+, S, A+, A, watch, embryonic
    follower_count: int = 0
    bio: str = ""
    expertise_tags: list[str] = field(default_factory=list)  # ["qec", "rl", "reasoning"]
    first_seen: str = ""                 # ISO 8601
    last_active: str = ""                # ISO 8601
    post_count: int = 0
    reply_count: int = 0
    avg_score: float = 0.0


@dataclass
class Post:
    """A single X post or reply. Immutable."""
    post_id: str
    author_handle: str
    text: str
    created_at: str                     # ISO 8601
    is_reply: bool = False
    reply_to_id: Optional[str] = None
    reply_to_handle: Optional[str] = None
    is_quote: bool = False
    quote_id: Optional[str] = None
    likes: int = 0
    views: int = 0
    reposts: int = 0
    replies: int = 0
    has_media: bool = False
    url: str = ""


@dataclass
class Signal:
    """Extracted signal from a post."""
    signal_id: str
    post_id: str
    author_handle: str
    signal_type: str                     # SignalType enum value
    score: float = 0.0                   # 0-100
    tier: str = "C"                      # S, A, B, C
    
    # Content
    summary: str = ""
    interpretation: str = ""
    
    # Quantum × AGI specific
    quantum_terms: int = 0               # Number of quantum keywords found
    agi_terms: int = 0                   # Number of AGI keywords found
    regime_terms: int = 0                # Number of regime-change phrases
    is_convergence: bool = False         # Multiple labs discussing same thing
    
    # Context
    lab: str = ""
    priority: str = ""                   # Account priority
    role: str = ""                       # Account role
    
    # Evidence
    evidence_quotes: list[str] = field(default_factory=list)  # Exact quotes
    
    # Metadata
    created_at: str = ""                 # ISO 8601
    extraction_version: str = "1.0"


@dataclass
class Convergence:
    """When multiple people discuss the same topic within a time window."""
    convergence_id: str
    topic: str                           # e.g., "decoder throughput", "rl scaling"
    topic_keywords: list[str] = field(default_factory=list)
    
    # Participants
    participants: list[str] = field(default_factory=list)  # handles
    labs_represented: list[str] = field(default_factory=list)
    
    # Timing
    first_signal_at: str = ""
    last_signal_at: str = ""
    time_window_hours: float = 0.0
    
    # Signals
    signal_ids: list[str] = field(default_factory=list)
    avg_score: float = 0.0
    
    # Interpretation
    interpretation: str = ""
    is_regime_change: bool = False
    
    created_at: str = ""


@dataclass
class PersonEdge:
    """Relationship between two people."""
    source_handle: str
    target_handle: str
    edge_type: str                       # "reply", "mention", "quote", "collaborator", "competitor"
    weight: float = 1.0                  # Strength of connection
    last_interaction: str = ""
    interaction_count: int = 0


@dataclass
class TopicEdge:
    """Relationship between a person and a topic."""
    handle: str
    topic: str                           # e.g., "qec", "rl_scaling", "fault_tolerance"
    weight: float = 1.0                  # How much they discuss this
    last_mention: str = ""


# ---------------------------------------------------------------------------
# Graph Structure
# ---------------------------------------------------------------------------

@dataclass
class FrontierGraph:
    """The complete intelligence graph."""
    persons: dict[str, Person] = field(default_factory=dict)          # handle → Person
    posts: dict[str, Post] = field(default_factory=dict)              # post_id → Post
    signals: dict[str, Signal] = field(default_factory=dict)          # signal_id → Signal
    convergences: dict[str, Convergence] = field(default_factory=dict) # convergence_id → Convergence
    
    # Edges
    person_edges: list[PersonEdge] = field(default_factory=list)
    topic_edges: list[TopicEdge] = field(default_factory=list)
    
    # Indexes
    signals_by_author: dict[str, list[str]] = field(default_factory=dict)  # handle → [signal_ids]
    signals_by_lab: dict[str, list[str]] = field(default_factory=dict)     # lab → [signal_ids]
    posts_by_author: dict[str, list[str]] = field(default_factory=dict)    # handle → [post_ids]
    convergences_by_topic: dict[str, list[str]] = field(default_factory=dict)  # topic → [convergence_ids]
