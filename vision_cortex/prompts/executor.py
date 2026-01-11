"""Prompt executor that maps PromptDefinitions to Vision Cortex agent pipelines."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

from vision_cortex.agents.base_agent import AgentContext
from vision_cortex.comms.message_bus import MessageBus
from vision_cortex.memory.memory_registry import MemoryRegistry
from vision_cortex.pipelines.system_build import SystemBuildOrchestrator
from vision_cortex.prompts.registry import resolve_alias
from vision_cortex.validators.safety import enforce_governance


class PromptExecutor:
    def __init__(
        self, bus: MessageBus, memory: Optional[MemoryRegistry] = None
    ) -> None:
        self.bus = bus
        self.memory = memory
        self.orchestrator = SystemBuildOrchestrator(bus=bus, memory=memory)

    def execute(
        self,
        prompt_or_alias: str,
        params: Optional[Dict[str, Any]] = None,
        confidence: float = 0.5,
    ) -> Dict[str, Any]:
        prompt = resolve_alias(prompt_or_alias)
        if prompt is None:
            return {"error": f"Unknown prompt or alias: {prompt_or_alias}"}

        governance = enforce_governance(prompt.governance_level)
        session_id = str(uuid.uuid4())
        context = AgentContext(
            session_id=session_id,
            task_id=str(uuid.uuid4()),
            governance_level=governance,
            confidence=confidence,
        )

        # Decide execution path based on prompt execution mode and confidence
        if prompt.execution == "auto" and confidence < prompt.confidence_threshold:
            return {
                "status": "deferred",
                "prompt_id": prompt.id,
                "reason": f"Confidence {confidence:.2f} below threshold {prompt.confidence_threshold:.2f}",
                "session_id": session_id,
            }

        # Build seed from prompt parameters merged with runtime params
        seed: Dict[str, Any] = {
            **prompt.parameters,
            **(params or {}),
            "session_id": session_id,
            "governance_level": governance,
            "prompt_id": prompt.id,
            "agents": prompt.agents,
        }

        result = self.orchestrator.run_build(seed, parallel=True)

        # Persist prompt execution record
        if self.memory:
            self.memory.persist_event(
                {
                    "type": "prompt_execution",
                    "prompt_id": prompt.id,
                    "level": prompt.level,
                    "execution_mode": prompt.execution,
                    "session_hash": session_id,
                    "confidence": confidence,
                    "governance_level": governance,
                    "result_summary": result.get("executive"),
                    "created_at": time.time(),
                }
            )

        return {
            "status": "completed",
            "prompt_id": prompt.id,
            "level": prompt.level,
            "session_id": session_id,
            "governance_level": governance,
            "result": result,
        }
