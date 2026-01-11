"""Ingestor agent: cleans, normalizes, and embeds observations."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List

from vision_cortex.agents.base_agent import AgentContext, BaseAgent


class IngestorAgent(BaseAgent):
    role = "ingestor"

    def run_task(
        self, context: AgentContext, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        raw = payload.get("raw", {}).get("observations", [])
        seen_titles = set()
        cleaned: List[Dict[str, Any]] = []
        for obs in raw:
            title = (obs.get("title") or "").strip()
            if title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())
            text = self._normalize(obs.get("text", ""))
            doc = {
                "title": title or "untitled",
                "text": text,
                "source": obs.get("source", "unknown"),
                "tags": obs.get("tags", []) + ["ingested"],
                "timestamp": obs.get("timestamp", time.time()),
                "tokens": len(text.split()),
            }
            cleaned.append(doc)
            if self.memory:
                self.memory.add_embedding(
                    text,
                    {
                        "title": doc["title"],
                        "source": doc["source"],
                        "session": context.session_id,
                    },
                )
        self.log_event("Ingested observations", context, {"count": len(cleaned)})
        self.publish_event("ingested", context, {"count": len(cleaned)})
        self.persist_memory(
            {
                "type": "ingested_batch",
                "session_hash": context.session_id,
                "task_id": context.task_id,
                "content": cleaned,
                "confidence": context.confidence,
                "created_at": time.time(),
            }
        )
        return {"cleaned": cleaned}

    def _normalize(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return text
