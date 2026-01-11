"""Tests for autonomous prompt registry and executor."""

from vision_cortex.comms.message_bus import MessageBus
from vision_cortex.memory.memory_registry import (
    InMemoryFirestore,
    InMemoryVectorStore,
    MemoryRegistry,
)
from vision_cortex.prompts import ALIASES, PROMPT_REGISTRY, list_prompts, resolve_alias
from vision_cortex.prompts.executor import PromptExecutor


def test_prompt_registry_has_all_levels():
    levels = {p.level for p in PROMPT_REGISTRY.values()}
    assert levels == set(range(1, 11)), "Expected prompts from L1 to L10"


def test_aliases_resolve_correctly():
    for alias, prompt_id in ALIASES.items():
        prompt = resolve_alias(alias)
        assert prompt is not None, f"Alias '{alias}' should resolve"
        assert prompt.id == prompt_id


def test_list_prompts_by_level():
    l3 = list_prompts(level=3)
    assert all(p.level == 3 for p in l3)
    assert len(l3) >= 2  # L3_GENERATE_PREDICTIONS, L3_SCENARIO_ANALYSIS


def test_list_prompts_by_tag():
    tagged = list_prompts(tag="prediction")
    assert len(tagged) >= 1
    assert any("prediction" in p.tags for p in tagged)


def test_executor_runs_prompt():
    bus = MessageBus()
    memory = MemoryRegistry(
        firestore=InMemoryFirestore(), vector_store=InMemoryVectorStore()
    )
    executor = PromptExecutor(bus=bus, memory=memory)

    result = executor.execute("scan", confidence=0.9)
    assert result["status"] == "completed"
    assert result["prompt_id"] == "L1_SYSTEM_SCAN"
    assert "result" in result


def test_executor_defers_low_confidence_auto():
    bus = MessageBus()
    memory = MemoryRegistry(
        firestore=InMemoryFirestore(), vector_store=InMemoryVectorStore()
    )
    executor = PromptExecutor(bus=bus, memory=memory)

    # L9_AUTO_PREDICT requires 0.85 confidence
    result = executor.execute("auto", confidence=0.5)
    assert result["status"] == "deferred"
    assert "below threshold" in result["reason"]
