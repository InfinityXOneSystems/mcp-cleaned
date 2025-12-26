"""Shared schemas and message contracts for Vision Cortex.

These dataclasses define the payloads exchanged between agents and the router.
They stay lightweight and dependency-free to ease testing and portability.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

REASONING_TAGS = {"REAL-TODAY", "EMERGING", "HYPOTHETICAL", "UNCERTAIN"}


def _now() -> float:
    return time.time()


def _id() -> str:
    return str(uuid.uuid4())


@dataclass
class Message:
    topic: str
    content: Dict[str, Any]
    session_id: str
    task_id: str
    correlation_id: str = field(default_factory=_id)
    governance_level: str = "LOW"
    sender: Optional[str] = None
    timestamp: float = field(default_factory=_now)


@dataclass
class DebateTurn:
    role: str
    agent: str
    position: str
    tag: str
    confidence: float
    rationale: str
    evidence: List[str] = field(default_factory=list)
    dissent: bool = False

    def __post_init__(self) -> None:
        if self.tag not in REASONING_TAGS:
            self.tag = "UNCERTAIN"


@dataclass
class DebateResult:
    topic: str
    turns: List[DebateTurn]
    consensus: Optional[str]
    consensus_confidence: float
    dissenting: List[DebateTurn]
    metrics: Dict[str, Any]


@dataclass
class ConfidenceSignal:
    score: float
    rationale: str
    tag: str = "UNCERTAIN"


@dataclass
class Observation:
    title: str
    text: str
    source: str
    timestamp: float
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class Prediction:
    statement: str
    horizon_days: int
    confidence: float
    tag: str
    signals: List[str] = field(default_factory=list)


@dataclass
class PlanStep:
    timeframe: str
    actions: List[str]
    risk: str
    success_metric: str


@dataclass
class PrioritizedAction:
    title: str
    priority: int
    confidence: float
    rationale: str
    governance_level: str
*** End
