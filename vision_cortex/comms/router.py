"""Smart Router for intent → agent mapping with governance awareness."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from vision_cortex.validators.safety import enforce_governance


class SmartRouter:
    def __init__(self, bus, governance_default: str = "HIGH") -> None:
        self._bus = bus
        self._logger = logging.getLogger("vision_cortex.router")
        self._agents: Dict[str, Any] = {}
        self._intent_map: Dict[str, str] = {}
        self._governance_default = governance_default

    def register_agent(self, role: str, agent: Any) -> None:
        self._agents[role] = agent
        self._logger.info("Registered agent %s", role)

    def map_intent(self, intent: str, role: str) -> None:
        self._intent_map[intent] = role

    def dispatch(self, intent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        role = self._intent_map.get(intent, intent)
        agent = self._agents.get(role)
        if not agent:
            raise ValueError(f"No agent registered for role '{role}' (intent '{intent}')")
        ctx = payload.get("context")
        if not ctx:
            raise ValueError("Context is required in payload for dispatch")
        ctx.governance_level = enforce_governance(ctx.governance_level)
        self._logger.info("Dispatching intent=%s to role=%s governance=%s", intent, role, ctx.governance_level)
        return agent.run_task(ctx, payload.get("data", {}))
*** End
