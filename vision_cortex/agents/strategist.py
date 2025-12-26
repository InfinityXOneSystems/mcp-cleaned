"""Strategist agent: backcasts plans from futures/predictions."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from vision_cortex.agents.base_agent import AgentContext, BaseAgent
from vision_cortex.schemas.contracts import PlanStep


class StrategistAgent(BaseAgent):
    role = "strategist"

    def run_task(self, context: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        scenarios = payload.get("scenarios", {}).get("scenarios", [])
        predictions = payload.get("predictions", {}).get("predictions", [])
        steps: List[Dict[str, Any]] = []
        for pred in predictions:
            steps.append(PlanStep(
                timeframe="0-30d",
                actions=["Define leading indicators", "Set up telemetry", "Run fast experiments"],
                risk="medium",
                success_metric="Signals tracked weekly",
            ).__dict__)
            steps.append(PlanStep(
                timeframe="30-90d",
                actions=["Invest in validated paths", "Harden data pipelines", "Align stakeholders"],
                risk="medium",
                success_metric="Validated experiments >60%",
            ).__dict__)
            steps.append(PlanStep(
                timeframe="90-365d",
                actions=["Scale proven strategies", "Automate monitoring", "Institutionalize learnings"],
                risk="low",
                success_metric="Run-rate impact sustained",
            ).__dict__)
        if scenarios:
            steps.append(PlanStep(
                timeframe="contingency",
                actions=["Maintain optionality", "Pre-negotiate pivots", "Simulate downside"],
                risk="high",
                success_metric="Response time <48h",
            ).__dict__)
        self.log_event("Generated strategy steps", context, {"count": len(steps)})
        self.publish_event("strategy", context, {"steps": len(steps)})
        self.persist_memory({
            "type": "strategy_steps",
            "session_hash": context.session_id,
            "task_id": context.task_id,
            "content": steps,
            "confidence": context.confidence,
            "created_at": time.time(),
        })
        return {"steps": steps}
*** End
