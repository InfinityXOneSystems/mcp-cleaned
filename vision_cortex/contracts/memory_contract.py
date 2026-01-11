"""
Memory Contract — Unified Memory Discipline
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md Article VIII

All memory operations MUST go through this contract.
Direct Firestore access is FORBIDDEN.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """Canonical memory entry types."""

    INFERENCE = "inference"
    AGENT_STATUS = "agent_status"
    PREDICTION = "prediction"
    DEBATE = "debate"
    SIGNAL = "signal"
    CONSENSUS = "consensus"
    MUTATION = "mutation"
    AUDIT_LOG = "audit_log"


@dataclass
class MemorySchema:
    """
    Mandatory schema for all memory entries.
    Enforced at write time — violations rejected.
    """

    session_hash: str
    type: MemoryType
    content: Dict[str, Any]
    confidence: float
    sources: List[str]
    agent_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    prompt_hash: Optional[str] = None

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if not self.session_hash:
            raise ValueError("session_hash is mandatory")
        if not self.agent_id:
            raise ValueError("agent_id is mandatory")

    @property
    def doc_id(self) -> str:
        """Generate deterministic document ID."""
        key = f"{self.session_hash}:{self.type.value}:{self.created_at.isoformat()}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_firestore_doc(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible document."""
        return {
            "session_hash": self.session_hash,
            "type": self.type.value,
            "content": self.content,
            "confidence": self.confidence,
            "sources": self.sources,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "prompt_hash": self.prompt_hash,
        }


class MemoryContract:
    """
    Contract governing all memory operations.

    Rules:
    1. All writes go through MemoryRegistry
    2. Agents may only read their own memory + shared memory
    3. Cross-agent memory access requires explicit permission
    4. Conversation logs are always persisted
    5. Audit trail is immutable
    """

    COLLECTION = "mcp_memory"

    # Agents that can read all memory
    OMNISCIENT_AGENTS = ["ceo", "validator"]

    # Memory types that are shared across agents
    SHARED_TYPES = [
        MemoryType.PREDICTION,
        MemoryType.SIGNAL,
        MemoryType.CONSENSUS,
        MemoryType.DEBATE,
    ]

    @staticmethod
    def can_read(agent_id: str, entry: MemorySchema) -> bool:
        """Check if agent can read this memory entry."""
        # Omniscient agents can read everything
        if any(omni in agent_id for omni in MemoryContract.OMNISCIENT_AGENTS):
            return True

        # Agents can read their own memory
        if entry.agent_id == agent_id:
            return True

        # All agents can read shared types
        if entry.type in MemoryContract.SHARED_TYPES:
            return True

        return False

    @staticmethod
    def can_write(agent_id: str, entry_type: MemoryType) -> bool:
        """Check if agent can write this memory type."""
        # All agents can write their own status
        if entry_type == MemoryType.AGENT_STATUS:
            return True

        # All agents can write audit logs
        if entry_type == MemoryType.AUDIT_LOG:
            return True

        # Type-specific permissions
        type_permissions = {
            MemoryType.INFERENCE: ["predictor", "visionary", "strategist"],
            MemoryType.PREDICTION: ["predictor", "visionary"],
            MemoryType.DEBATE: ["validator", "ceo"],
            MemoryType.SIGNAL: ["crawler", "ingestor", "organizer"],
            MemoryType.CONSENSUS: ["ceo", "validator"],
            MemoryType.MUTATION: ["evolver", "ceo"],  # Note: evolver may be added
        }

        allowed_agents = type_permissions.get(entry_type, [])
        return any(agent in agent_id for agent in allowed_agents)

    @staticmethod
    def validate_write(agent_id: str, entry: MemorySchema) -> List[str]:
        """Validate a memory write operation. Returns list of violations."""
        violations = []

        if not MemoryContract.can_write(agent_id, entry.type):
            violations.append(
                f"Agent {agent_id} not authorized to write {entry.type.value}"
            )

        if entry.agent_id != agent_id:
            violations.append(f"Agent {agent_id} cannot write as {entry.agent_id}")

        return violations
