"""Vision Cortex core behavior tests."""

from vision_cortex.agents import (
    CrawlerAgent,
    DocumentorAgent,
    IngestorAgent,
    OrganizerAgent,
    PredictorAgent,
    StrategistAgent,
    ValidatorAgent,
    VisionaryAgent,
)
from vision_cortex.agents.base_agent import AgentContext
from vision_cortex.comms.message_bus import MessageBus
from vision_cortex.memory.memory_registry import (
    InMemoryFirestore,
    InMemoryVectorStore,
    MemoryRegistry,
)
from vision_cortex.pipelines.daily_ingestion import DailyIngestionPipeline
from vision_cortex.pipelines.debate_cycle import DebateCycle


def _registry() -> MemoryRegistry:
    return MemoryRegistry(
        firestore=InMemoryFirestore(), vector_store=InMemoryVectorStore()
    )


def test_message_bus_publish_subscribe() -> None:
    bus = MessageBus()
    received = []

    def handler(msg):
        received.append(msg)

    bus.subscribe("logs", handler)
    bus.publish("logs", {"ping": True})
    assert received and received[0]["ping"] is True


def test_daily_ingestion_pipeline_runs() -> None:
    bus = MessageBus()
    registry = _registry()
    crawler = CrawlerAgent(name="crawler_01", role="crawler", bus=bus, memory=registry)
    ingestor = IngestorAgent(
        name="ingestor_01", role="ingestor", bus=bus, memory=registry
    )
    organizer = OrganizerAgent(
        name="organizer_01", role="organizer", bus=bus, memory=registry
    )
    validator = ValidatorAgent(
        name="validator_01", role="validator", bus=bus, memory=registry
    )
    pipeline = DailyIngestionPipeline(crawler, ingestor, organizer, validator)

    result = pipeline.run(
        session_id="sess-1",
        task_id="task-1",
        seed={
            "sources": [
                {
                    "title": "AI model release",
                    "url": "https://example.com",
                    "content": "New AI model released",
                }
            ]
        },
    )
    assert result["outputs"]["validated"]["risks"] is not None


def test_debate_cycle_produces_document() -> None:
    bus = MessageBus()
    registry = _registry()
    predictor = PredictorAgent(
        name="predictor_01", role="predictor", bus=bus, memory=registry
    )
    visionary = VisionaryAgent(
        name="visionary_01", role="visionary", bus=bus, memory=registry
    )
    strategist = StrategistAgent(
        name="strategist_01", role="strategist", bus=bus, memory=registry
    )
    validator = ValidatorAgent(
        name="validator_01", role="validator", bus=bus, memory=registry
    )
    documentor = DocumentorAgent(
        name="documentor_01", role="documentor", bus=bus, memory=registry
    )

    debate = DebateCycle(predictor, visionary, strategist, validator, documentor)
    organized = {
        "clusters": {
            "ai": [{"title": "AI release", "text": "increase in ai capability"}]
        }
    }
    output = debate.run(session_id="sess-2", task_id="task-2", organized=organized)
    assert "report" in output["document"]
    assert output["debate"].consensus is not None


def test_evolver_generates_improvements() -> None:
    bus = MessageBus()
    registry = _registry()
    from vision_cortex.agents.evolver import EvolverAgent

    evolver = EvolverAgent(name="evolver_01", role="evolver", bus=bus, memory=registry)
    ctx = AgentContext(session_id="sess-3", task_id="task-3")
    result = evolver.run_task(
        ctx, {"validations": {"risks": [{"type": "test"}], "contradictions": []}}
    )
    assert result["improvements"]
