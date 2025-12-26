"""
Agent Factory - Spawns role-based agents with LangChain integration
Creates Visionary, Strategist, Builder, and Critic agents
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging
import asyncio
from datetime import datetime
import json

from .models import AgentConfig, AgentRole, TaskResult, TaskStatus
from .memory_layer import MemoryLayer

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base agent interface"""

    def __init__(self, config: AgentConfig, memory: Optional[MemoryLayer] = None):
        """Initialize agent"""
        self.config = config
        self.memory = memory
        self.role = config.role
        self.execution_history = []
        self.logger = logging.getLogger(f"Agent.{self.role}")

    @abstractmethod
    async def execute(self, objective: str, context: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Execute task - must be implemented by subclasses"""
        pass

    async def _store_execution(self, result: TaskResult) -> None:
        """Store execution result in memory"""
        if self.memory:
            self.memory.store_task_result(
                task_id=result.task_id,
                agent_role=result.agent_role,
                objective=result.objective,
                result=result.result,
                confidence=result.confidence,
                reasoning=result.reasoning,
            )

    async def think(self, prompt: str) -> str:
        """Thinking routine - would call LLM in production"""
        # Placeholder for LangChain LLM integration
        return f"[{self.role.upper()}] Analyzed: {prompt[:100]}..."


class VisionaryAgent(BaseAgent):
    """Visionary agent - generates long-term vision and emerging opportunities"""

    async def execute(self, objective: str, context: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Generate visionary insights"""
        start_time = datetime.now()
        task_id = f"vision_{datetime.now().timestamp()}"

        try:
            self.logger.info(f"Executing vision task: {objective}")

            # Use LLM for vision generation (placeholder)
            thinking_result = await self.think(objective)

            # Simulate vision generation
            vision = {
                "objective": objective,
                "vision": "Emerging AI-driven systems will reshape knowledge work",
                "timeframe": "5-10 years",
                "confidence": 0.82,
                "opportunities": [
                    "Autonomous reasoning systems",
                    "Multi-agent collaboration frameworks",
                    "Self-improving knowledge bases"
                ]
            }

            result = TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                agent_role=self.role.value,
                objective=objective,
                result=vision,
                confidence=vision["confidence"],
                reasoning=thinking_result,
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                created_at=start_time,
                completed_at=datetime.now(),
            )

            await self._store_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Vision task failed: {e}")
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                agent_role=self.role.value,
                objective=objective,
                result=None,
                confidence=0.0,
                reasoning=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                created_at=start_time,
                error=str(e),
            )


class StrategistAgent(BaseAgent):
    """Strategist agent - develops actionable strategies from vision"""

    async def execute(self, objective: str, context: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Develop strategic plan"""
        start_time = datetime.now()
        task_id = f"strat_{datetime.now().timestamp()}"

        try:
            self.logger.info(f"Executing strategy task: {objective}")

            thinking_result = await self.think(objective)

            # Simulate strategy development
            strategy = {
                "objective": objective,
                "phases": [
                    {
                        "phase": 1,
                        "name": "Foundation",
                        "duration_weeks": 12,
                        "key_activities": ["Architecture design", "Prototype development"]
                    },
                    {
                        "phase": 2,
                        "name": "Scaling",
                        "duration_weeks": 16,
                        "key_activities": ["Multi-agent integration", "Performance optimization"]
                    }
                ],
                "resources": ["Team of 4 engineers", "Cloud infrastructure", "ML compute"],
                "risks": ["Integration complexity", "Scaling challenges"],
            }

            result = TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                agent_role=self.role.value,
                objective=objective,
                result=strategy,
                confidence=0.78,
                reasoning=thinking_result,
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                created_at=start_time,
                completed_at=datetime.now(),
            )

            await self._store_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Strategy task failed: {e}")
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                agent_role=self.role.value,
                objective=objective,
                result=None,
                confidence=0.0,
                reasoning=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                created_at=start_time,
                error=str(e),
            )


class BuilderAgent(BaseAgent):
    """Builder agent - implements strategies and builds solutions"""

    async def execute(self, objective: str, context: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Build implementation"""
        start_time = datetime.now()
        task_id = f"build_{datetime.now().timestamp()}"

        try:
            self.logger.info(f"Executing build task: {objective}")

            thinking_result = await self.think(objective)

            # Simulate build execution
            implementation = {
                "objective": objective,
                "components": [
                    {
                        "name": "Agent Framework",
                        "status": "completed",
                        "code_lines": 2500,
                        "tests": 145
                    },
                    {
                        "name": "Memory Layer",
                        "status": "completed",
                        "code_lines": 800,
                        "tests": 42
                    }
                ],
                "deployment": {
                    "containerized": True,
                    "scalable": True,
                    "monitoring": True
                },
            }

            result = TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                agent_role=self.role.value,
                objective=objective,
                result=implementation,
                confidence=0.88,
                reasoning=thinking_result,
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                created_at=start_time,
                completed_at=datetime.now(),
            )

            await self._store_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Build task failed: {e}")
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                agent_role=self.role.value,
                objective=objective,
                result=None,
                confidence=0.0,
                reasoning=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                created_at=start_time,
                error=str(e),
            )


class CriticAgent(BaseAgent):
    """Critic agent - validates, challenges, and identifies risks"""

    async def execute(self, objective: str, context: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Validate and critique"""
        start_time = datetime.now()
        task_id = f"critic_{datetime.now().timestamp()}"

        try:
            self.logger.info(f"Executing critique task: {objective}")

            thinking_result = await self.think(objective)

            # Simulate critique
            critique = {
                "objective": objective,
                "assessment": "Comprehensive approach with solid foundations",
                "strengths": [
                    "Well-architected",
                    "Scalable design",
                    "Good test coverage"
                ],
                "weaknesses": [
                    "Complex state management",
                    "Need better documentation"
                ],
                "risks": {
                    "high": ["Integration delays"],
                    "medium": ["Performance under load"],
                    "low": ["Documentation gaps"]
                },
                "recommendations": [
                    "Implement circuit breakers",
                    "Add comprehensive monitoring",
                    "Increase test coverage to 90%"
                ]
            }

            result = TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                agent_role=self.role.value,
                objective=objective,
                result=critique,
                confidence=0.85,
                reasoning=thinking_result,
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                created_at=start_time,
                completed_at=datetime.now(),
            )

            await self._store_execution(result)
            return result

        except Exception as e:
            self.logger.error(f"Critique task failed: {e}")
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                agent_role=self.role.value,
                objective=objective,
                result=None,
                confidence=0.0,
                reasoning=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                created_at=start_time,
                error=str(e),
            )


class AgentFactory:
    """Factory for creating and managing agents"""

    AGENT_MAP = {
        AgentRole.VISIONARY: VisionaryAgent,
        AgentRole.STRATEGIST: StrategistAgent,
        AgentRole.BUILDER: BuilderAgent,
        AgentRole.CRITIC: CriticAgent,
    }

    def __init__(self, memory: Optional[MemoryLayer] = None):
        """Initialize factory"""
        self.memory = memory or MemoryLayer()
        self.agents = {}
        # Simple in-memory registry for created agent instances
        self._registry: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("AgentFactory")

    def create_agent(self, role: str, config: Optional[AgentConfig] = None) -> BaseAgent:
        """Create an agent by role"""
        try:
            # Convert string to AgentRole if needed
            if isinstance(role, str):
                role = AgentRole(role.lower())

            if role not in self.AGENT_MAP:
                raise ValueError(f"Unknown agent role: {role}")

            # Use provided config or create default
            if config is None:
                config = AgentConfig(role=role)

            agent_class = self.AGENT_MAP[role]
            agent = agent_class(config, self.memory)

            self.agents[role.value] = agent
            self.logger.info(f"✓ Created {role.value} agent")

            return agent

        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}")
            raise

    def get_agent(self, role: str) -> Optional[BaseAgent]:
        """Get an existing agent"""
        return self.agents.get(role)

    async def execute_task(
        self,
        role: str,
        objective: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Execute a task using an agent"""
        try:
            agent = self.get_agent(role)
            if not agent:
                agent = self.create_agent(role)

            return await agent.execute(objective, context)

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            raise

    async def execute_pipeline(
        self,
        roles: List[str],
        objectives: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[TaskResult]:
        """Execute sequential pipeline across agents"""
        results = []

        try:
            for role, objective in zip(roles, objectives):
                result = await self.execute_task(role, objective, context)
                results.append(result)
                
                # Update context with previous result for next agent
                if context is None:
                    context = {}
                context["previous_result"] = result.result

            self.logger.info(f"✓ Pipeline completed with {len(results)} tasks")
            return results

    def create_agent_instance(self, template: AgentConfig, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a persisted agent instance (in-memory registry).

        Returns a dict with instance_id and stored config.
        """
        import uuid

        # Merge template config with overrides
        cfg = template.dict()
        if overrides:
            cfg.update(overrides)

        instance_id = f"agent_{uuid.uuid4().hex[:8]}"

        stored = {
            "id": instance_id,
            "role": cfg.get("role"),
            "name": cfg.get("name", f"{cfg.get('role')}_instance"),
            "config": cfg,
            "created_at": datetime.now().isoformat()
        }

        # persist in simple registry
        self._registry[instance_id] = stored

        # eagerly create runtime agent (so execute calls work)
        try:
            self.create_agent(stored["role"], AgentConfig(**cfg))
        except Exception:
            # ignore creation errors; registry remains
            pass

        return stored

    def list_agent_instances(self) -> List[Dict[str, Any]]:
        """Return list of created agent instances"""
        return list(self._registry.values())

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            raise

    def list_agents(self) -> Dict[str, str]:
        """List all available agents"""
        return {role.value: role.value for role in AgentRole}

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics on created agents"""
        return {
            "total_agents": len(self.agents),
            "agents": list(self.agents.keys()),
            "memory_stats": self.memory.get_memory_stats(),
        }
