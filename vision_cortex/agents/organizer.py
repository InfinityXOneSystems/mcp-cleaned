"""Organizer agent: structures knowledge into themes and clusters."""
from __future__ import annotations

import collections
import time
from typing import Any, Dict, List

from vision_cortex.agents.base_agent import AgentContext, BaseAgent

THEME_KEYWORDS = {
    "economics": ["inflation", "gdp", "economy", "market", "trade"],
    "ai": ["model", "ai", "ml", "llm", "neural"],
    "governance": ["policy", "regulation", "governance"],
    "ethics": ["ethic", "bias", "fair"],
    "security": ["security", "attack", "threat", "vulnerability"],
    "strategy": ["strategy", "plan", "roadmap", "initiative"],
}


class OrganizerAgent(BaseAgent):
    role = "organizer"

    def run_task(self, context: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = payload.get("cleaned", {}).get("cleaned", [])
        clusters: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
        for doc in cleaned:
            topic = self._classify(doc["text"])
            clusters[topic].append(doc)
        summary = {k: len(v) for k, v in clusters.items()}
        self.log_event("Organized documents", context, {"clusters": summary})
        self.publish_event("organized", context, summary)
        self.persist_memory({
            "type": "organized_batch",
            "session_hash": context.session_id,
            "task_id": context.task_id,
            "content": {k: v for k, v in clusters.items()},
            "confidence": context.confidence,
            "created_at": time.time(),
        })
        return {"clusters": clusters, "summary": summary}

    def _classify(self, text: str) -> str:
        lowered = text.lower()
        for theme, keywords in THEME_KEYWORDS.items():
            if any(k in lowered for k in keywords):
                return theme
        return "general"
*** End
