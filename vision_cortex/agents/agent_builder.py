"""AgentBuilder: LLM-backed agent that generates new agent scaffolds/specs.

It implements `run_task(context, payload)` and returns a small agent spec JSON.
"""
from __future__ import annotations

import logging
import json
import time
from typing import Dict, Any

from vision_cortex.agents.base_agent import AgentContext, BaseAgent
from vision_cortex.llm.adapter import call as llm_call

logger = logging.getLogger(__name__)


class AgentBuilderAgent(BaseAgent):
    role = "agent_builder"

    def run_task(self, context: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        objective = payload.get("objective") or payload.get("name") or "Create helper agent"
        prompt = (
            f"You are an agent generator. Create a concise agent spec for: {objective}.\n"
            "Return a JSON with keys: name, role, capabilities (list), interface (endpoints or methods), dependencies (pip packages)."
        )

        llm_resp = llm_call(prompt)
        # Attempt to parse JSON from the model response; if not possible, wrap text
        try:
            spec = json.loads(llm_resp)
        except Exception:
            spec = {"name": f"agent_{int(time.time())}", "role": "generated", "raw": llm_resp}

        self.log_event("Generated agent spec", context, {"spec": spec})
        return {"spec": spec, "confidence": 0.6}
