"""
Communication Contract — Inter-Agent Message Discipline
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md

All agent-to-agent communication MUST go through this contract.
Direct calls between agents are FORBIDDEN.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ChannelType(Enum):
    """Canonical communication channel types."""

    AGENT_OUTPUT = "agent_output"  # Agent → Bus
    DEBATE_ARENA = "debate_arena"  # Multi-agent debate
    CONSENSUS = "consensus"  # Final decisions
    BROADCAST = "broadcast"  # System-wide announcements
    DIRECT = "direct"  # Point-to-point (rare, audited)


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5  # Triggers immediate processing


@dataclass
class MessageSchema:
    """
    Mandatory schema for all inter-agent messages.
    Enforced by MessageBus — violations rejected.
    """

    message_id: str
    channel: ChannelType
    sender_id: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    recipients: List[str] = field(default_factory=list)  # Empty = broadcast
    requires_ack: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 3600  # Time to live
    correlation_id: Optional[str] = None  # For request/response chains

    def __post_init__(self):
        if not self.message_id:
            # Generate deterministic message ID
            key = f"{self.sender_id}:{self.channel.value}:{self.timestamp.isoformat()}"
            self.message_id = hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "channel": self.channel.value,
            "sender_id": self.sender_id,
            "payload": self.payload,
            "priority": self.priority.value,
            "recipients": self.recipients,
            "requires_ack": self.requires_ack,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "correlation_id": self.correlation_id,
        }


@dataclass
class DebateMessage:
    """
    Specialized message for debate arena.
    Used for multi-agent consensus building.
    """

    debate_id: str
    round_number: int
    sender_id: str
    position: str  # "support", "oppose", "abstain"
    argument: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if self.position not in ["support", "oppose", "abstain"]:
            raise ValueError(f"Invalid position: {self.position}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")


class CommunicationContract:
    """
    Contract governing all inter-agent communication.

    Rules:
    1. All messages go through MessageBus
    2. Direct agent calls are forbidden
    3. All messages are logged for audit
    4. Debate messages require confidence scores
    5. Emergency messages bypass normal queue
    """

    # Predefined channels
    CHANNELS = {
        "agent.crawler.output": ChannelType.AGENT_OUTPUT,
        "agent.ingestor.output": ChannelType.AGENT_OUTPUT,
        "agent.organizer.output": ChannelType.AGENT_OUTPUT,
        "agent.predictor.output": ChannelType.AGENT_OUTPUT,
        "agent.visionary.output": ChannelType.AGENT_OUTPUT,
        "agent.strategist.output": ChannelType.AGENT_OUTPUT,
        "agent.ceo.output": ChannelType.AGENT_OUTPUT,
        "agent.validator.output": ChannelType.AGENT_OUTPUT,
        "agent.documentor.output": ChannelType.AGENT_OUTPUT,
        "debate.arena": ChannelType.DEBATE_ARENA,
        "consensus.builder": ChannelType.CONSENSUS,
        "system.broadcast": ChannelType.BROADCAST,
    }

    # Agents that can send to specific channels
    CHANNEL_PERMISSIONS: Dict[str, List[str]] = {
        "debate.arena": ["predictor", "visionary", "strategist", "validator", "ceo"],
        "consensus.builder": ["ceo", "validator"],
        "system.broadcast": ["ceo", "validator"],
    }

    @staticmethod
    def can_send(agent_id: str, channel: str) -> bool:
        """Check if agent can send to this channel."""
        # Agents can always send to their own output channel
        if channel == f"agent.{agent_id}.output":
            return True

        # Check specific channel permissions
        if channel in CommunicationContract.CHANNEL_PERMISSIONS:
            allowed = CommunicationContract.CHANNEL_PERMISSIONS[channel]
            return any(agent in agent_id for agent in allowed)

        # Default: allow output channels
        if channel.startswith("agent.") and channel.endswith(".output"):
            return agent_id in channel

        return False

    @staticmethod
    def can_receive(agent_id: str, channel: str) -> bool:
        """Check if agent can receive from this channel."""
        # All agents can receive broadcasts
        if channel == "system.broadcast":
            return True

        # All agents can receive consensus
        if channel == "consensus.builder":
            return True

        # Debate participants can receive debate messages
        if channel == "debate.arena":
            return agent_id in CommunicationContract.CHANNEL_PERMISSIONS.get(
                channel, []
            )

        # CEO and Validator can receive all agent outputs
        if any(omni in agent_id for omni in ["ceo", "validator"]):
            return True

        return False

    @staticmethod
    def validate_message(msg: MessageSchema) -> List[str]:
        """Validate a message before sending. Returns list of violations."""
        violations = []

        if not msg.sender_id:
            violations.append("sender_id is mandatory")

        if not msg.payload:
            violations.append("payload cannot be empty")

        if msg.priority == MessagePriority.EMERGENCY and not msg.requires_ack:
            violations.append("EMERGENCY messages must require acknowledgement")

        return violations
