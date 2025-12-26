"""System build pipeline that chains Vision Cortex agents for end-to-end builds.

This pipeline is tailored for VS Code automation and background builds: it
crawls inputs, ingests, organizes, strategizes, forecasts, validates, and
documents, then runs the evolver loop for improvements.
"""
from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from vision_cortex.agents import (
    CEOAgent,
    CrawlerAgent,
    DocumentorAgent,
    EvolverAgent,
    IngestorAgent,
    OrganizerAgent,
    PredictorAgent,
    StrategistAgent,
    ValidatorAgent,
    VisionaryAgent,
)
from vision_cortex.agents.base_agent import AgentContext
from vision_cortex.memory.memory_registry import MemoryRegistry
from vision_cortex.validators.safety import enforce_governance


class SystemBuildOrchestrator:
    def __init__(self, bus: Any, memory: Optional[MemoryRegistry] = None, governance_level: str = "HIGH") -> None:
        self.bus = bus
        self.memory = memory
        self.governance_level = enforce_governance(governance_level)
        # Agent instances reuse the same bus/memory to share context.
        self.crawler = CrawlerAgent(name="crawler", role="crawler", bus=bus, memory=memory, governance_level=self.governance_level)
        self.ingestor = IngestorAgent(name="ingestor", role="ingestor", bus=bus, memory=memory, governance_level=self.governance_level)
        self.organizer = OrganizerAgent(name="organizer", role="organizer", bus=bus, memory=memory, governance_level=self.governance_level)
        self.visionary = VisionaryAgent(name="visionary", role="visionary", bus=bus, memory=memory, governance_level=self.governance_level)
        self.strategist = StrategistAgent(name="strategist", role="strategist", bus=bus, memory=memory, governance_level=self.governance_level)
        self.predictor = PredictorAgent(name="predictor", role="predictor", bus=bus, memory=memory, governance_level=self.governance_level)
        self.validator = ValidatorAgent(name="validator", role="validator", bus=bus, memory=memory, governance_level=self.governance_level)
        self.documentor = DocumentorAgent(name="documentor", role="documentor", bus=bus, memory=memory, governance_level=self.governance_level)
        self.ceo = CEOAgent(name="ceo", role="ceo", bus=bus, memory=memory, governance_level=self.governance_level)
        self.evolver = EvolverAgent(name="evolver", role="evolver", bus=bus, memory=memory, governance_level=self.governance_level)

    def run_build(self, seed: Dict[str, Any], parallel: bool = True) -> Dict[str, Any]:
        session_id = seed.get("session_id") or str(uuid.uuid4())
        governance = enforce_governance(seed.get("governance_level", self.governance_level))
        context = AgentContext(session_id=session_id, task_id=str(uuid.uuid4()), governance_level=governance, confidence=0.55)

        # Phase 1: crawl and ingest can run in parallel for speed.
        observations: List[Dict[str, Any]] = []
        ingested: Dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=2 if parallel else 1) as pool:
            futures = {
                pool.submit(self.crawler.run_task, context, seed): "crawl",
                pool.submit(self.ingestor.run_task, context, seed): "ingest",
            }
            for future in as_completed(futures):
                label = futures[future]
                result = future.result()
                if label == "crawl":
                    observations = result.get("observations", [])
                elif label == "ingest":
                    ingested = result

        organized = self.organizer.run_task(context, {"observations": observations, "ingested": ingested})
        strategy = self.strategist.run_task(context, {"organized": organized})
        vision = self.visionary.run_task(context, {"strategy": strategy, "seed": seed})
        forecast = self.predictor.run_task(context, {"vision": vision})
        validation = self.validator.run_task(context, {"forecast": forecast, "organized": organized})
        doc = self.documentor.run_task(context, {"vision": vision, "strategy": strategy, "validation": validation})
        executive = self.ceo.run_task(context, {"doc": doc, "forecast": forecast, "validation": validation})
        evolved = self.evolver.run_task(context, {"build": executive, "vision": vision, "strategy": strategy})

        summary = {
            "session_id": session_id,
            "governance_level": governance,
            "observations": len(observations),
            "organized": organized,
            "strategy": strategy,
            "vision": vision,
            "forecast": forecast,
            "validation": validation,
            "documentation": doc,
            "executive": executive,
            "evolved": evolved,
            "timestamp": time.time(),
        }
        if self.memory:
            self.memory.persist_event({
                "type": "system_build_summary",
                "session_hash": session_id,
                "content": summary,
                "confidence": 0.65,
                "governance_level": governance,
                "created_at": summary["timestamp"],
            })
        self.bus.publish("build_completed", {"session_id": session_id, "summary": summary})
        return summary
