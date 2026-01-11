from vision_cortex.comms.message_bus import MessageBus
from vision_cortex.comms.pubsub_bridge import PubSubBridge
from vision_cortex.memory.memory_registry import (
    InMemoryFirestore,
    InMemoryVectorStore,
    MemoryRegistry,
)
from vision_cortex.vscode_agent import VSCodeAgent


def test_pubsub_bridge_persists_bus_logs():
    bus = MessageBus()
    memory = MemoryRegistry(
        firestore=InMemoryFirestore(), vector_store=InMemoryVectorStore()
    )
    bridge = PubSubBridge(bus=bus, memory=memory, thread_ids=["thread-1"])

    bus.publish(
        "logs", {"message": "hello", "context": {"session_id": "s1", "confidence": 0.7}}
    )

    stored = memory.firestore.query("mcp_memory")
    assert stored, "expected persisted events"
    assert stored[0]["type"] == "bus_log"
    assert "thread-1" in stored[0]["thread_ids"]


def test_vscode_agent_background_build():
    bus = MessageBus()
    memory = MemoryRegistry(
        firestore=InMemoryFirestore(), vector_store=InMemoryVectorStore()
    )
    agent = VSCodeAgent(bus=bus, memory=memory, max_workers=2)

    future = agent.run_background_build({"seed": {"sources": []}})
    result = future.result(timeout=5)

    assert "summary" not in result  # orchestrator returns summary without nesting
    assert "observations" in result
    assert agent.pending_jobs() == 0
