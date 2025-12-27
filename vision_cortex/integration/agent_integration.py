"""Agent integration helper: creates a SimpleBus, registers premade agents,
and returns a configured SmartRouter for use by the gateway.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from vision_cortex.comms.router import SmartRouter
from vision_cortex.agents.base_agent import AgentContext

# Import some premade agents (exists in repo)
from vision_cortex.agents.crawler import CrawlerAgent
from vision_cortex.agents.ingestor import IngestorAgent
from vision_cortex.agents.predictor import PredictorAgent
from vision_cortex.agents.visionary import VisionaryAgent
from vision_cortex.agents.agent_builder import AgentBuilderAgent

logger = logging.getLogger(__name__)


class SimpleBus:
    """Minimal in-memory message bus used for local routing/logging.

    Provides `publish(topic, payload)` and `subscribe(topic, handler)`.
    This is intentionally tiny — production systems should provide a
    durable bus implementation.
    """

    def __init__(self) -> None:
        self._subs: Dict[str, list[Callable[[Dict[str, Any]], None]]] = {}

    def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        # Log then call subscribers
        logger.debug("bus.publish topic=%s payload=%s", topic, payload)
        for handler in self._subs.get(topic, []):
            try:
                handler(payload)
            except Exception:
                logger.exception("bus handler error for topic %s", topic)

    def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        self._subs.setdefault(topic, []).append(handler)


def init_agents() -> SmartRouter:
    """Create bus, register a small set of premade agents and return router.

    The returned router can be attached to the FastAPI app (e.g.,
    `app.state.agent_router = init_agents()`) so endpoints can dispatch.
    """
    bus = SimpleBus()
    router = SmartRouter(bus, governance_default="LOW")

    # Instantiate a few premade agents and register them by role
    try:
        crawler = CrawlerAgent(name="crawler", role="crawler", bus=bus)
        ingestor = IngestorAgent(name="ingestor", role="ingestor", bus=bus)
        predictor = PredictorAgent(name="predictor", role="predictor", bus=bus)
        visionary = VisionaryAgent(name="visionary", role="visionary", bus=bus)

        router.register_agent("crawler", crawler)
        router.register_agent("ingestor", ingestor)
        router.register_agent("predictor", predictor)
        router.register_agent("visionary", visionary)
        # Register the AgentBuilder LLM-backed agent
        builder = AgentBuilderAgent(name="agent_builder", role="agent_builder", bus=bus)
        router.register_agent("agent_builder", builder)

        # Map common intents to agents (optional)
        router.map_intent("discover", "crawler")
        router.map_intent("ingest", "ingestor")
        router.map_intent("forecast", "predictor")
        router.map_intent("vision", "visionary")
        router.map_intent("build_agent", "agent_builder")

        logger.info("Initialized default agents: crawler, ingestor, predictor, visionary")
    except Exception:
        logger.exception("Failed to initialize some premade agents")

    return router
