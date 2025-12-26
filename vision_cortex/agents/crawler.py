"""Crawler agent: gathers external signals from provided seeds."""
from __future__ import annotations

import time
from typing import Any, Dict, List
from urllib.parse import urlparse

from vision_cortex.agents.base_agent import AgentContext, BaseAgent
from vision_cortex.schemas.contracts import Observation


class CrawlerAgent(BaseAgent):
    role = "crawler"

    def run_task(self, context: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        seed = payload.get("seed") or {}
        sources: List[Dict[str, Any]] = seed.get("sources", [])
        observations: List[Dict[str, Any]] = []
        for src in sources:
            title = src.get("title") or src.get("url") or "untitled"
            url = src.get("url", "")
            text = (src.get("content") or "").strip()
            hostname = urlparse(url).netloc or "unknown"
            confidence = 0.55 + min(len(text) / 2000.0, 0.25)
            obs = Observation(
                title=title,
                text=text or f"No content provided for {title}",
                source=url or hostname,
                timestamp=time.time(),
                tags=["crawler", hostname],
                confidence=min(confidence, 0.95),
            )
            observations.append(obs.__dict__)
            self.log_event("Collected observation", context, {"source": url, "confidence": obs.confidence})
        self.publish_event("observations", context, {"count": len(observations)})
        self.persist_memory({
            "type": "observation_batch",
            "session_hash": context.session_id,
            "task_id": context.task_id,
            "content": observations,
            "confidence": context.confidence,
            "created_at": time.time(),
        })
        return {"observations": observations, "sources": len(sources)}
*** End
