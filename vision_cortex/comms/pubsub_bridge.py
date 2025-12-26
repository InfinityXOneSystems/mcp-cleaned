"""Bridge between Vision Cortex message bus and external threads (chat/UI).

- Forwards bus topics into chat threads via MemoryRegistry for persistence.
- Allows chat threads to publish messages back onto the internal bus.
- Supports fan-out to multiple thread_ids; uses governance-aware payloads.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Optional

from vision_cortex.comms.message_bus import MessageBus
from vision_cortex.memory.memory_registry import MemoryRegistry
from vision_cortex.validators.safety import enforce_governance


class PubSubBridge:
    def __init__(self, bus: MessageBus, memory: MemoryRegistry, thread_ids: Optional[Iterable[str]] = None) -> None:
        self.bus = bus
        self.memory = memory
        self.thread_ids = set(thread_ids or [])
        self.logger = logging.getLogger("vision_cortex.pubsub_bridge")
        self.bus.subscribe("logs", self._handle_logs)

    def register_thread(self, thread_id: str) -> None:
        self.thread_ids.add(thread_id)

    def _handle_logs(self, payload: Dict[str, Any]) -> None:
        governance = enforce_governance(str(payload.get("governance_level", "HIGH")))
        record = {
            "type": "bus_log",
            "thread_ids": list(self.thread_ids) or ["default"],
            "content": payload,
            "governance_level": governance,
            "session_hash": payload.get("context", {}).get("session_id", "n/a"),
            "created_at": payload.get("timestamp"),
            "confidence": payload.get("context", {}).get("confidence", 0.0),
        }
        try:
            self.memory.persist_event(record)
        except Exception as exc:
            self.logger.error("Failed to persist bus log: %s", exc)

    def send_to_bus(self, topic: str, payload: Dict[str, Any], governance_level: str = "HIGH") -> None:
        payload = dict(payload)
        payload["governance_level"] = enforce_governance(governance_level)
        self.bus.publish(topic, payload)

    def send_to_threads(self, payload: Dict[str, Any], governance_level: str = "HIGH") -> None:
        governance = enforce_governance(governance_level)
        record = {
            "type": "chat_thread_message",
            "thread_ids": list(self.thread_ids) or ["default"],
            "content": payload,
            "governance_level": governance,
            "created_at": payload.get("timestamp"),
        }
        self.memory.persist_event(record)
