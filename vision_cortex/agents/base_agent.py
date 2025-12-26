"""Base agent class for Vision Cortex roles.

Provides structured logging, message publication, and optional memory writes.
All agents must implement `run_task` to perform their role-specific logic.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol

from vision_cortex.memory.memory_registry import MemoryRegistry


class MessageBus(Protocol):
    def publish(self, topic: str, payload: Dict[str, Any]) -> None: ...

    def subscribe(self, topic: str, handler: Any) -> None: ...


@dataclass
class AgentContext:
    session_id: str
    task_id: str
    governance_level: str = "LOW"
    confidence: float = 0.0
    tags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaseAgent:
    name: str
    role: str
    bus: MessageBus
    governance_level: str = "LOW"
    memory: Optional[MemoryRegistry] = None

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(f"vision_cortex.agents.{self.role}")

    def log_event(self, message: str, context: AgentContext, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "timestamp": time.time(),
            "event_id": str(uuid.uuid4()),
            "agent": self.name,
            "role": self.role,
            "governance_level": self.governance_level,
            "message": message,
            "context": context.__dict__,
            "extra": extra or {},
        }
        self.logger.info("%s | ctx=%s | extra=%s", message, context.__dict__, extra or {})
        self.bus.publish("logs", payload)
        if self.memory:
            self.memory.persist_event({
                "type": "agent_status",
                "agent": self.name,
                "role": self.role,
                "content": payload,
                "confidence": context.confidence,
                "governance_level": self.governance_level,
                "session_hash": context.session_id,
                "created_at": payload["timestamp"],
            })
        return payload

    def publish_event(self, topic: str, context: AgentContext, content: Dict[str, Any]) -> None:
        event = {
            "timestamp": time.time(),
            "event_id": str(uuid.uuid4()),
            "from": self.name,
            "role": self.role,
            "context": context.__dict__,
            "content": content,
        }
        self.bus.publish(topic, event)

    def persist_memory(self, record: Dict[str, Any]) -> None:
        if self.memory:
            self.memory.persist_event(record)
        else:
            self.logger.debug("No memory registry configured; skipping persist for %s", record.get("type"))

    def run_task(self, context: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Agents must implement run_task()")
