"""
REST API endpoints for autonomy stack
Provides /agents, /tasks, /memory, /models, /pipeline endpoints
"""
from fastapi import APIRouter, HTTPException, Header, Query, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import asyncio

from .agent_factory import AgentFactory
from .task_queue import TaskQueue
from .memory_layer import MemoryLayer
from .security import SecurityManager, get_security_manager
from .models import (
    AgentConfig, AgentRole, TaskRequest, TaskResult, TaskStatus,
    MemoryEntry, PipelineConfig, ModelExperimentConfig
)

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str


class AgentListResponse(BaseModel):
    """List of available agents"""
    agents: Dict[str, str]
    count: int


class TaskSubmitResponse(BaseModel):
    """Task submission response"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str
    status: str
    result: Optional[Any] = None
    info: Optional[Any] = None


class MemoryQueryRequest(BaseModel):
    """Memory query request"""
    query: str
    collection: str = "shared"
    n_results: int = 5
    agent_role: Optional[str] = None


class MemoryStoreRequest(BaseModel):
    """Memory store request"""
    content: str
    metadata: Dict[str, Any]
    agent_role: Optional[str] = None


class PipelineExecuteRequest(BaseModel):
    """Pipeline execution request"""
    pipeline_name: str
    agents: List[str]
    objectives: List[str]
    context: Optional[Dict[str, Any]] = None


def get_agent_factory() -> AgentFactory:
    """Dependency: get agent factory"""
    return AgentFactory()


def get_task_queue() -> TaskQueue:
    """Dependency: get task queue"""
    return TaskQueue()


def get_memory_layer() -> MemoryLayer:
    """Dependency: get memory layer"""
    return MemoryLayer()


def verify_api_key(x_api_key: str = Header(...), security: SecurityManager = Depends(get_security_manager)) -> bool:
    """Verify API key from header"""
    if not security.validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def create_routes(
    agent_factory: Optional[AgentFactory] = None,
    task_queue: Optional[TaskQueue] = None,
    memory_layer: Optional[MemoryLayer] = None
) -> APIRouter:
    """Create autonomy stack routes"""
    router = APIRouter(prefix="/autonomy", tags=["autonomy"])

    # Initialize components
    factory = agent_factory or AgentFactory()
    queue = task_queue or TaskQueue()
    memory = memory_layer or MemoryLayer()

    # ===== HEALTH CHECKS =====
    @router.get("/health", response_model=HealthResponse)
    async def health_check(security: SecurityManager = Depends(get_security_manager)):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "message": f"Autonomy stack operational. Safe mode: {security.is_safe_mode()}"
        }

    # ===== AGENT MANAGEMENT =====
    @router.get("/agents", response_model=AgentListResponse)
    async def list_agents(api_key: bool = Depends(verify_api_key)):
        """List available agents"""
        agents = factory.list_agents()
        return {
            "agents": agents,
            "count": len(agents)
        }

    @router.get("/agent_templates", response_model=List[AgentConfig])
    async def get_agent_templates(api_key: bool = Depends(verify_api_key)):
        """Return a set of pre-made agent templates for UI dropdowns.

        Each template includes `role`, `name`, `description`, and `config` defaults.
        """
        templates = [
            AgentConfig(
                role=AgentRole.VISIONARY,
                name="Visionary (Futures)",
                description="Generates high-level visions, scenarios, and strategic narratives.",
                config={"creativity": 0.9, "depth": "long", "max_tokens": 800},
            ),
            AgentConfig(
                role=AgentRole.STRATEGIST,
                name="Strategist (Plans)",
                description="Transforms visions into prioritized plans and OKRs.",
                config={"creativity": 0.6, "horizon_days": 90, "max_actions": 10},
            ),
            AgentConfig(
                role=AgentRole.BUILDER,
                name="Builder (Executor)",
                description="Produces runnable artifacts, code, and infra steps.",
                config={"tools": ["git","docker"], "max_retries": 2},
            ),
            AgentConfig(
                role=AgentRole.CRITIC,
                name="Critic (Validator)",
                description="Reviews proposals, finds gaps, and scores risks.",
                config={"strictness": "high", "checks": ["security","compliance"]},
            ),
        ]
        return templates

    class AgentCreateRequest(BaseModel):
        template: AgentConfig
        overrides: Optional[Dict[str, Any]] = None

    @router.post("/agents/create")
    async def create_agent_instance(
        body: AgentCreateRequest,
        api_key: bool = Depends(verify_api_key)
    ):
        """Create and persist an agent instance from a template plus optional overrides."""
        try:
            stored = factory.create_agent_instance(body.template, body.overrides)
            return {
                "created": True,
                "instance": stored
            }
        except Exception as e:
            logger.error(f"Create agent instance failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/agents/{role}/execute")
    async def execute_agent(
        role: str,
        request: TaskRequest,
        api_key: bool = Depends(verify_api_key)
    ) -> TaskResult:
        """Execute a task with an agent"""
        try:
            result = await factory.execute_task(role, request.objective, request.context)
            return result
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/agents/stats")
    async def get_agent_stats(api_key: bool = Depends(verify_api_key)):
        """Get agent statistics"""
        return factory.get_agent_stats()

    # ===== TASK MANAGEMENT =====
    @router.post("/tasks/submit", response_model=TaskSubmitResponse)
    async def submit_task(
        request: TaskRequest,
        api_key: bool = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        """Submit a task to the queue"""
        try:
            task_id = queue.submit_task(
                agent_role=request.agent_role.value,
                objective=request.objective,
                context=request.context,
                priority=request.priority,
                timeout=request.timeout_seconds
            )
            return {
                "task_id": task_id,
                "status": "queued",
                "message": f"Task submitted successfully"
            }
        except Exception as e:
            logger.error(f"Task submission failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
    async def get_task_status(
        task_id: str,
        api_key: bool = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        """Get task status"""
        try:
            return queue.get_task_status(task_id)
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/tasks/{task_id}")
    async def cancel_task(
        task_id: str,
        api_key: bool = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        """Cancel a task"""
        try:
            success = queue.cancel_task(task_id)
            return {
                "task_id": task_id,
                "cancelled": success,
                "message": "Task cancelled" if success else "Failed to cancel task"
            }
        except Exception as e:
            logger.error(f"Task cancellation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/tasks/queue/stats")
    async def get_queue_stats(api_key: bool = Depends(verify_api_key)):
        """Get queue statistics"""
        return queue.get_queue_stats()

    # ===== MEMORY MANAGEMENT =====
    @router.post("/memory/store")
    async def store_memory(
        request: MemoryStoreRequest,
        api_key: bool = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        """Store entry in memory"""
        try:
            import uuid
            from datetime import datetime

            entry = MemoryEntry(
                id=str(uuid.uuid4()),
                content=request.content,
                metadata=request.metadata,
                agent_role=request.agent_role,
                timestamp=datetime.now()
            )

            collection = request.agent_role if request.agent_role else "shared"
            success = memory.store(entry, collection=collection)

            return {
                "success": success,
                "entry_id": entry.id,
                "collection": collection
            }
        except Exception as e:
            logger.error(f"Memory store failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/memory/retrieve")
    async def retrieve_memory(
        request: MemoryQueryRequest,
        api_key: bool = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        """Retrieve memories by semantic similarity"""
        try:
            results = memory.retrieve(
                query=request.query,
                collection=request.collection,
                n_results=request.n_results,
                agent_role=request.agent_role
            )
            return {
                "query": request.query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/memory/stats")
    async def get_memory_stats(api_key: bool = Depends(verify_api_key)):
        """Get memory statistics"""
        return memory.get_memory_stats()

    @router.delete("/memory/{collection}")
    async def clear_memory(
        collection: str = "shared",
        api_key: bool = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        """Clear a memory collection"""
        try:
            success = memory.clear_collection(collection)
            return {
                "collection": collection,
                "cleared": success
            }
        except Exception as e:
            logger.error(f"Memory clear failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ===== PIPELINE EXECUTION =====
    @router.post("/pipeline/execute")
    async def execute_pipeline(
        request: PipelineExecuteRequest,
        api_key: bool = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        """Execute multi-agent pipeline"""
        try:
            if len(request.agents) != len(request.objectives):
                raise ValueError("Agents and objectives lists must have same length")

            results = await factory.execute_pipeline(
                roles=request.agents,
                objectives=request.objectives,
                context=request.context
            )

            return {
                "pipeline_name": request.pipeline_name,
                "status": "completed",
                "results": [r.dict() for r in results],
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ===== MODEL MANAGEMENT =====
    @router.post("/models/experiment")
    async def create_experiment(
        config: ModelExperimentConfig,
        api_key: bool = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        """Create a model experiment"""
        try:
            import uuid
            experiment_id = str(uuid.uuid4())[:8]

            experiment = {
                "experiment_id": experiment_id,
                "name": config.name,
                "model_type": config.model_type,
                "task": config.task,
                "status": "created",
                "batch_size": config.batch_size,
                "epochs": config.epochs,
                "created_at": datetime.now().isoformat()
            }

            return experiment
        except Exception as e:
            logger.error(f"Experiment creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/models/experiments")
    async def list_experiments(api_key: bool = Depends(verify_api_key)):
        """List model experiments"""
        return {
            "experiments": [],
            "total": 0,
            "message": "No experiments yet"
        }

    return router


# Import datetime for responses
from datetime import datetime
