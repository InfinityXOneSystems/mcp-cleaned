"""Validator agent: critiques outputs and detects contradictions."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from vision_cortex.agents.base_agent import AgentContext, BaseAgent
from vision_cortex.validators.safety import enforce_governance


class ValidatorAgent(BaseAgent):
    role = "validator"

    def run_task(self, context: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        predictions = payload.get("predictions", {}).get("predictions", [])
        scenarios = payload.get("scenarios", {}).get("scenarios", [])
        contradictions = self._find_contradictions(predictions)
        risks = []
        if contradictions:
            risks.append({"type": "contradiction", "details": contradictions})
        if scenarios:
            risks.append({"type": "scenario_uncertainty", "count": len(scenarios)})
        context.governance_level = enforce_governance(context.governance_level)
        self.log_event("Validation results", context, {"contradictions": len(contradictions), "risks": len(risks)})
        self.publish_event("validation", context, {"risks": risks})
        self.persist_memory({
            "type": "validation_report",
            "session_hash": context.session_id,
            "task_id": context.task_id,
            "content": {"risks": risks, "contradictions": contradictions},
            "confidence": context.confidence,
            "created_at": time.time(),
        })
        return {"risks": risks, "contradictions": contradictions}

    def _find_contradictions(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        contradictions: List[Dict[str, Any]] = []
        for pred in predictions:
            stmt = pred.get("statement", "").lower()
            if "increase" in stmt and "decrease" in stmt:
                contradictions.append({"statement": pred.get("statement"), "reason": "increase vs decrease"})
        return contradictions
