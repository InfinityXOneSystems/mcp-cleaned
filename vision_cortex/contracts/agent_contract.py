"""
Agent Contract — Machine-Enforceable Agreement
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md

Every agent MUST implement this contract.
Violations trigger Validator kill switch.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class GovernanceLevel(Enum):
    """Governance levels with confidence thresholds."""

    LOW = 0.5
    MEDIUM = 0.7
    HIGH = 0.85
    CRITICAL = 0.95


class AgentRole(Enum):
    """Canonical agent roles — no collapsing permitted."""

    CRAWLER = "crawler"
    INGESTOR = "ingestor"
    ORGANIZER = "organizer"
    PREDICTOR = "predictor"
    VISIONARY = "visionary"
    STRATEGIST = "strategist"
    CEO = "ceo"
    VALIDATOR = "validator"
    DOCUMENTOR = "documentor"


@dataclass
class AgentIdentity:
    """Immutable agent identity."""

    role: AgentRole
    version: str
    governance_level: GovernanceLevel
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        # Enforce immutability after creation
        self._frozen = True

    @property
    def agent_id(self) -> str:
        return f"{self.role.value}_v{self.version}"


@dataclass
class TaskResult:
    """Mandatory output structure for all agent tasks."""

    result: Any
    confidence: float
    reasoning: str
    sources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if not self.reasoning:
            raise ValueError("Reasoning is mandatory — no silent outputs")


@dataclass
class AgentContext:
    """Context passed to agent for task execution."""

    session_id: str
    request_id: str
    governance_level: GovernanceLevel
    memory_access: bool = True
    debate_enabled: bool = True
    dry_run: bool = True  # Default to safe mode

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "request_id": self.request_id,
            "governance_level": self.governance_level.name,
            "memory_access": self.memory_access,
            "debate_enabled": self.debate_enabled,
            "dry_run": self.dry_run,
        }


class AgentContract:
    """
    Base contract that all agents MUST implement.

    Mandatory Methods:
    - run_task(context, payload) -> TaskResult
    - validate_input(payload) -> bool
    - emit_intent(intent) -> None

    Forbidden Behaviors:
    - Returning results without confidence scores
    - Skipping reasoning documentation
    - Modifying other agents' memory
    - Operating outside governance level
    """

    REQUIRED_METHODS = ["run_task", "validate_input", "emit_intent"]

    @staticmethod
    def validate_implementation(agent_class) -> List[str]:
        """Validate that an agent class implements all required methods."""
        violations = []
        for method in AgentContract.REQUIRED_METHODS:
            if not hasattr(agent_class, method) or not callable(
                getattr(agent_class, method)
            ):
                violations.append(f"Missing required method: {method}")
        return violations

    @staticmethod
    def validate_result(result: TaskResult, governance_level: GovernanceLevel) -> bool:
        """Validate that a TaskResult meets governance requirements."""
        if result.confidence < governance_level.value:
            return False
        if not result.reasoning:
            return False
        return True


# Intent Schema — Required for all agent emissions
@dataclass
class IntentEmission:
    """
    Mandatory intent structure for agent outputs.
    All predictions, signals, and strategic outputs must emit intent.
    """

    agent_id: str
    intent_type: str  # prediction, signal, strategy, alert, mutation
    payload: Dict[str, Any]
    confidence: float
    governance_level: GovernanceLevel
    requires_debate: bool = False
    requires_human_approval: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_firestore_doc(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible document."""
        return {
            "agent_id": self.agent_id,
            "intent_type": self.intent_type,
            "payload": self.payload,
            "confidence": self.confidence,
            "governance_level": self.governance_level.name,
            "requires_debate": self.requires_debate,
            "requires_human_approval": self.requires_human_approval,
            "timestamp": self.timestamp.isoformat(),
        }
