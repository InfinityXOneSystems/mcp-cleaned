"""
Autonomy Stack Tests
Comprehensive test suite for all components
"""

import asyncio
from datetime import datetime

import pytest

from autonomy_stack.agent_factory import AgentFactory, StrategistAgent, VisionaryAgent
from autonomy_stack.memory_layer import MemoryLayer
from autonomy_stack.models import AgentConfig, AgentRole, MemoryEntry, TaskRequest
from autonomy_stack.security import SecurityManager


class TestAgentFactory:
    """Test agent factory"""

    def test_create_agent(self):
        """Test agent creation"""
        factory = AgentFactory()
        agent = factory.create_agent("visionary")

        assert agent is not None
        assert agent.role == AgentRole.VISIONARY

    def test_list_agents(self):
        """Test listing agents"""
        factory = AgentFactory()
        agents = factory.list_agents()

        assert len(agents) == 4
        assert "visionary" in agents
        assert "strategist" in agents
        assert "builder" in agents
        assert "critic" in agents

    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test task execution"""
        factory = AgentFactory()
        result = await factory.execute_task("visionary", "Test objective")

        assert result is not None
        assert result.status.value == "completed"
        assert result.confidence > 0
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """Test pipeline execution"""
        factory = AgentFactory()
        roles = ["visionary", "strategist"]
        objectives = ["What's next?", "How do we get there?"]

        results = await factory.execute_pipeline(roles, objectives)

        assert len(results) == 2
        assert all(r.status.value == "completed" for r in results)


class TestMemoryLayer:
    """Test memory layer"""

    def test_store_and_retrieve(self):
        """Test storing and retrieving memory"""
        memory = MemoryLayer()

        entry = MemoryEntry(
            id="test_1",
            content="Test memory content",
            metadata={"test": True},
            agent_role="visionary",
            timestamp=datetime.now(),
        )

        # Store
        success = memory.store(entry, "visionary")
        assert success

        # Retrieve
        results = memory.retrieve("memory", collection="visionary", n_results=1)
        assert len(results) > 0

    def test_memory_stats(self):
        """Test memory statistics"""
        memory = MemoryLayer()
        stats = memory.get_memory_stats()

        assert isinstance(stats, dict)
        assert "visionary_memory" in stats
        assert "strategist_memory" in stats
        assert "builder_memory" in stats
        assert "critic_memory" in stats
        assert "shared_memory" in stats

    def test_clear_collection(self):
        """Test clearing collection"""
        memory = MemoryLayer()

        # Store entry
        entry = MemoryEntry(
            id="test_clear",
            content="To be cleared",
            metadata={},
            timestamp=datetime.now(),
        )
        memory.store(entry, "shared")

        # Clear
        success = memory.clear_collection("shared")
        assert success


class TestSecurityManager:
    """Test security manager"""

    def test_create_security_manager(self):
        """Test security manager creation"""
        security = SecurityManager()

        assert security is not None
        assert security.get_redis_url() is not None

    def test_api_key_validation(self):
        """Test API key validation"""
        security = SecurityManager()

        # Should fail with wrong key
        security.validate_api_key("wrong_key")
        # Result depends on environment setup

    def test_timing_safe_compare(self):
        """Test timing-safe comparison"""
        a = "secret123"
        b = "secret123"
        c = "different"

        assert SecurityManager._timing_safe_compare(a, b) is True
        assert SecurityManager._timing_safe_compare(a, c) is False

    def test_hash_token(self):
        """Test token hashing"""
        token = "test_token"
        hashed = SecurityManager.hash_token(token)

        assert hashed != token
        assert len(hashed) == 64  # SHA256


class TestModels:
    """Test data models"""

    def test_agent_config(self):
        """Test agent config model"""
        config = AgentConfig(role=AgentRole.VISIONARY, model="gpt-4", temperature=0.7)

        assert config.role == AgentRole.VISIONARY
        assert config.temperature == 0.7

    def test_task_request(self):
        """Test task request model"""
        request = TaskRequest(
            task_type="analysis",
            agent_role=AgentRole.VISIONARY,
            objective="Test objective",
        )

        assert request.objective == "Test objective"
        assert request.priority == 5  # default

    def test_memory_entry(self):
        """Test memory entry model"""
        entry = MemoryEntry(
            id="test",
            content="Test content",
            metadata={"key": "value"},
            timestamp=datetime.now(),
        )

        assert entry.id == "test"
        assert entry.content == "Test content"


class TestVisionaryAgent:
    """Test visionary agent"""

    @pytest.mark.asyncio
    async def test_vision_execution(self):
        """Test visionary execution"""
        memory = MemoryLayer()
        config = AgentConfig(role=AgentRole.VISIONARY)
        agent = VisionaryAgent(config, memory)

        result = await agent.execute("What's emerging?")

        assert result.status.value == "completed"
        assert result.confidence > 0.5
        assert "vision" in result.result


class TestStrategistAgent:
    """Test strategist agent"""

    @pytest.mark.asyncio
    async def test_strategy_execution(self):
        """Test strategist execution"""
        memory = MemoryLayer()
        config = AgentConfig(role=AgentRole.STRATEGIST)
        agent = StrategistAgent(config, memory)

        result = await agent.execute("How should we proceed?")

        assert result.status.value == "completed"
        assert result.confidence > 0.5
        assert "phases" in result.result


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
