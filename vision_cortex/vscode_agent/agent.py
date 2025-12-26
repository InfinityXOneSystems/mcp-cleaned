"""VS Code automation agent bridging chat threads, pub/sub, and system builds.

Capabilities:
- Subscribe to Vision Cortex bus and forward to chat threads (PubSubBridge).
- Accept chat commands to trigger background system builds using Auto-Builder pipeline.
- Run builds in parallel with bounded worker pool.
"""
from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from vision_cortex.comms.message_bus import MessageBus
from vision_cortex.comms.pubsub_bridge import PubSubBridge
from vision_cortex.memory.memory_registry import MemoryRegistry
from vision_cortex.pipelines.system_build import SystemBuildOrchestrator
from vision_cortex.validators.safety import enforce_governance


class VSCodeAgent:
    def __init__(self, bus: MessageBus, memory: MemoryRegistry, max_workers: int = 4, governance_level: str = "HIGH") -> None:
        self.bus = bus
        self.memory = memory
        self.governance_level = enforce_governance(governance_level)
        self.bridge = PubSubBridge(bus=bus, memory=memory)
        self.orchestrator = SystemBuildOrchestrator(bus=bus, memory=memory, governance_level=self.governance_level)
        self.pool = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger("vision_cortex.vscode_agent")
        self._futures: List[Future] = []
        self._lock = threading.Lock()
        self.bus.subscribe("build_completed", self._handle_build_completed)

    def register_chat_thread(self, thread_id: str) -> None:
        self.bridge.register_thread(thread_id)

    def run_background_build(self, seed: Dict[str, Any]) -> Future:
        seed = dict(seed)
        seed["governance_level"] = enforce_governance(seed.get("governance_level", self.governance_level))
        future = self.pool.submit(self.orchestrator.run_build, seed)
        with self._lock:
            self._futures.append(future)
        self.logger.info("Queued background build session=%s", seed.get("session_id"))
        return future

    def run_parallel_builds(self, seeds: List[Dict[str, Any]]) -> List[Future]:
        futures: List[Future] = []
        for seed in seeds:
            futures.append(self.run_background_build(seed))
        return futures

    def handle_chat_command(self, thread_id: str, command: Dict[str, Any]) -> None:
        self.register_chat_thread(thread_id)
        kind = command.get("type")
        payload = command.get("payload", {})
        if kind == "build":
            self.run_background_build(payload)
        elif kind == "broadcast":
            self.bridge.send_to_bus("chat_broadcast", {"thread_id": thread_id, "payload": payload}, governance_level=self.governance_level)
        else:
            self.bridge.send_to_threads({"thread_id": thread_id, "notice": f"Unknown command: {kind}"}, governance_level=self.governance_level)

    def _handle_build_completed(self, payload: Dict[str, Any]) -> None:
        summary = payload.get("summary", {})
        self.bridge.send_to_threads({"event": "build_completed", "summary": summary}, governance_level=self.governance_level)

    def pending_jobs(self) -> int:
        with self._lock:
            return sum(1 for f in self._futures if not f.done())

    def shutdown(self) -> None:
        self.pool.shutdown(wait=False)
