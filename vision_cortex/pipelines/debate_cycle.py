"""Debate and consensus cycle for Vision Cortex.

Orchestrates predictor → visionary → strategist → validator → documentor to
produce a consensus view and log dissent.
"""
from __future__ import annotations

import statistics
import time
from typing import Dict, Any

from vision_cortex.agents.base_agent import AgentContext, BaseAgent
from vision_cortex.schemas.contracts import DebateResult, DebateTurn


class DebateCycle:
    def __init__(
        self,
        predictor: BaseAgent,
        visionary: BaseAgent,
        strategist: BaseAgent,
        validator: BaseAgent,
        documentor: BaseAgent,
    ) -> None:
        self.predictor = predictor
        self.visionary = visionary
        self.strategist = strategist
        self.validator = validator
        self.documentor = documentor

    def run(self, session_id: str, task_id: str, organized: Dict[str, Any]) -> Dict[str, Any]:
        ctx = AgentContext(session_id=session_id, task_id=task_id, governance_level="MEDIUM")
        preds = self.predictor.run_task(ctx, {"organized": organized})
        visions = self.visionary.run_task(ctx, preds)
        strategies = self.strategist.run_task(ctx, {"scenarios": visions, "predictions": preds})
        validations = self.validator.run_task(ctx, {"predictions": preds, "scenarios": visions})
        actions = strategies.get("steps", [])
        doc = self.documentor.run_task(ctx, {"predictions": preds, "steps": strategies, "actions": actions})

        turns = [
            DebateTurn(role="predictor", agent=self.predictor.name, position=str(p.get("statement")), tag=p.get("tag", "UNCERTAIN"), confidence=p.get("confidence", 0.5), rationale="trend synthesis")
            for p in preds.get("predictions", [])
        ]
        turns.extend(
            DebateTurn(role="validator", agent=self.validator.name, position=str(r), tag="REAL-TODAY", confidence=0.6, rationale="policy enforcement", dissent=True)
            for r in validations.get("risks", [])
        )
        consensus, consensus_conf = self._compute_consensus(turns)
        result = DebateResult(
            topic="vision_cortex_debate",
            turns=turns,
            consensus=consensus,
            consensus_confidence=consensus_conf,
            dissenting=[t for t in turns if t.dissent],
            metrics={"turns": len(turns), "dissent": len([t for t in turns if t.dissent])},
        )
        return {
            "predictions": preds,
            "visions": visions,
            "strategies": strategies,
            "validations": validations,
            "document": doc,
            "debate": result,
        }

    def _compute_consensus(self, turns: Any) -> Any:
        if not turns:
            return None, 0.0
        confidences = [t.confidence for t in turns if not t.dissent]
        if not confidences:
            return "no-consensus", 0.0
        median_conf = statistics.median(confidences)
        return "proceed", median_conf
