"""CEO agent: prioritizes decisions and allocates attention."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from vision_cortex.agents.base_agent import AgentContext, BaseAgent
from vision_cortex.schemas.contracts import PrioritizedAction


class CEOAgent(BaseAgent):
    role = "ceo"

    def run_task(self, context: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        steps = payload.get("steps", {}).get("steps") or payload.get("steps") or []
        prioritized: List[Dict[str, Any]] = []
        for idx, step in enumerate(steps):
            priority = idx + 1
            rationale = f"Timeframe {step.get('timeframe')} influences sequencing."
            action = PrioritizedAction(
                title=f"Execute plan for {step.get('timeframe')}",
                priority=priority,
                confidence=max(0.5, 0.9 - 0.05 * idx),
                rationale=rationale,
                governance_level=self.governance_level,
            )
            prioritized.append(action.__dict__)
        self.log_event("Prioritized actions", context, {"count": len(prioritized)})
        self.publish_event("priorities", context, {"count": len(prioritized)})
        self.persist_memory({
            "type": "prioritized_actions",
            "session_hash": context.session_id,
            "task_id": context.task_id,
            "content": prioritized,
            "confidence": context.confidence,
            "created_at": time.time(),
        })
        return {"actions": prioritized}
*** End
