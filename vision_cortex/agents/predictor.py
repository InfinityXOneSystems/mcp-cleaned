"""Predictor agent: produces forecasts from organized clusters."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from vision_cortex.agents.base_agent import AgentContext, BaseAgent
from vision_cortex.schemas.contracts import Prediction


class PredictorAgent(BaseAgent):
    role = "predictor"

    def run_task(self, context: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        clusters = payload.get("organized", {}).get("clusters", {})
        predictions: List[Dict[str, Any]] = []
        for topic, docs in clusters.items():
            horizon = max(7, min(90, len(docs) * 7))
            confidence = min(0.9, 0.4 + 0.05 * len(docs))
            stmt = f"{topic.capitalize()} momentum expected over next {horizon} days with moderate volatility."
            pred = Prediction(
                statement=stmt,
                horizon_days=horizon,
                confidence=confidence,
                tag="EMERGING" if len(docs) < 3 else "REAL-TODAY",
                signals=[d.get("title", "") for d in docs][:5],
            )
            predictions.append(pred.__dict__)
            self.log_event("Generated prediction", context, {"topic": topic, "confidence": confidence})
        self.publish_event("predictions", context, {"count": len(predictions)})
        self.persist_memory({
            "type": "prediction_batch",
            "session_hash": context.session_id,
            "task_id": context.task_id,
            "content": predictions,
            "confidence": context.confidence,
            "created_at": time.time(),
        })
        return {"predictions": predictions}
