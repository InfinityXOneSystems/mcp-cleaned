"""Documentor agent: produces human-readable outputs and summaries."""

from __future__ import annotations

import time
from typing import Any, Dict, List

from vision_cortex.agents.base_agent import AgentContext, BaseAgent


class DocumentorAgent(BaseAgent):
    role = "documentor"

    def run_task(
        self, context: AgentContext, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        predictions = payload.get("predictions", {}).get("predictions", [])
        steps = payload.get("steps", {}).get("steps") or payload.get("steps") or []
        actions = payload.get("actions") or []
        report = self._build_report(predictions, steps, actions)
        self.log_event("Generated report", context, {"chars": len(report)})
        self.publish_event("reports", context, {"status": "ready"})
        self.persist_memory(
            {
                "type": "document",
                "session_hash": context.session_id,
                "task_id": context.task_id,
                "content": {"report": report},
                "confidence": context.confidence,
                "created_at": time.time(),
            }
        )
        return {"report": report}

    def _build_report(
        self,
        predictions: List[Dict[str, Any]],
        steps: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
    ) -> str:
        lines: List[str] = []
        if predictions:
            lines.append("Predictions:")
            for pred in predictions:
                lines.append(
                    f"- ({pred.get('tag','')}) {pred.get('statement')} [conf={pred.get('confidence',0):.2f}]"
                )
        if steps:
            lines.append("\nPlans:")
            for step in steps:
                actions_text = "; ".join(step.get("actions", []))
                lines.append(
                    f"- {step.get('timeframe')}: {actions_text} (risk={step.get('risk')})"
                )
        if actions:
            lines.append("\nPriorities:")
            for act in actions:
                lines.append(
                    f"- P{act.get('priority')}: {act.get('title')} [conf={act.get('confidence',0):.2f}]"
                )
        return "\n".join(lines)
