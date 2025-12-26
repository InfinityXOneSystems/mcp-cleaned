"""Daily ingestion pipeline for Vision Cortex.

Executes Crawler -> Ingestor -> Organizer -> Validator with governance-aware
logging. Intended to be run on curated daily seed lists.
"""
from __future__ import annotations

from typing import Dict, Any
from datetime import datetime

from vision_cortex.agents.base_agent import AgentContext, BaseAgent


class DailyIngestionPipeline:
    def __init__(self, crawler: BaseAgent, ingestor: BaseAgent, organizer: BaseAgent, validator: BaseAgent):
        self.crawler = crawler
        self.ingestor = ingestor
        self.organizer = organizer
        self.validator = validator

    def run(self, session_id: str, task_id: str, seed: Dict[str, Any]) -> Dict[str, Any]:
        ctx = AgentContext(session_id=session_id, task_id=task_id, governance_level="LOW")
        raw = self._step("crawler", self.crawler, ctx, {"seed": seed})
        cleaned = self._step("ingestor", self.ingestor, ctx, {"raw": raw})
        organized = self._step("organizer", self.organizer, ctx, {"cleaned": cleaned})
        validated = self._step("validator", self.validator, ctx, {"organized": organized})
        return {
            "session_id": session_id,
            "task_id": task_id,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "outputs": {
                "raw": raw,
                "cleaned": cleaned,
                "organized": organized,
                "validated": validated,
            },
        }

    def _step(self, name: str, agent: BaseAgent, ctx: AgentContext, payload: Dict[str, Any]) -> Any:
        agent.log_event(f"Executing step {name}", ctx, {"payload_keys": list(payload.keys())})
        return agent.run_task(ctx, payload)
