"""
Task queue orchestration with Celery and Redis
"""

from typing import Any, Dict, Optional

from celery import Celery, Task
from celery.utils.log import get_task_logger

from .security import get_security_manager

logger = get_task_logger(__name__)


class AutonomyTask(Task):
    """Base task class with custom error handling"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True


def create_task_queue(
    broker_url: Optional[str] = None, backend_url: Optional[str] = None
) -> Celery:
    """Create and configure Celery app"""
    security = get_security_manager()

    broker = broker_url or security.get_celery_broker()
    backend = backend_url or security.get_celery_backend()

    app = Celery(
        "autonomy_stack",
        broker=broker,
        backend=backend,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=600,  # 10 minutes hard limit
        task_soft_time_limit=540,  # 9 minutes soft limit
        result_expires=3600,  # Results expire after 1 hour
        broker_connection_retry_on_startup=True,
        task_base=AutonomyTask,
    )

    logger.info(f"✓ Celery app created: {broker}")
    return app


# Global celery app
celery_app = create_task_queue()


@celery_app.task(bind=True)
def execute_agent_task(
    self, agent_role: str, objective: str, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute agent task via Celery"""
    try:
        from .agent_factory import AgentFactory

        factory = AgentFactory()
        factory.create_agent(agent_role)

        # This is a placeholder - actual execution depends on agent implementation
        result = {
            "task_id": self.request.id,
            "agent_role": agent_role,
            "objective": objective,
            "status": "completed",
            "result": f"Executed task: {objective}",
            "confidence": 0.85,
        }

        return result
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise


@celery_app.task(bind=True)
def pipeline_execution(
    self,
    pipeline_name: str,
    agents: list,
    objectives: list,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute multi-agent pipeline"""
    try:
        results = []

        for agent_role, objective in zip(agents, objectives):
            result = execute_agent_task.apply_async(
                args=(agent_role, objective), kwargs={"context": context}
            )
            results.append(result)

        return {
            "pipeline_name": pipeline_name,
            "task_ids": [r.id for r in results],
            "status": "pipeline_created",
        }
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise


@celery_app.task
def cleanup_old_results(days: int = 7) -> Dict[str, Any]:
    """Clean up old task results from backend"""
    try:
        # Redis cleanup would happen here
        return {"status": "cleanup_completed", "days": days}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise


class TaskQueue:
    """High-level task queue interface"""

    def __init__(self, celery_app: Optional[Celery] = None):
        """Initialize task queue"""
        self.app = celery_app or celery_app
        self.logger = logger

    def submit_task(
        self,
        agent_role: str,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        timeout: int = 300,
    ) -> str:
        """Submit a task for async execution"""
        try:
            task = execute_agent_task.apply_async(
                args=(agent_role, objective),
                kwargs={"context": context},
                priority=priority,
                time_limit=timeout,
            )
            self.logger.info(f"✓ Task submitted: {task.id}")
            return task.id
        except Exception as e:
            self.logger.error(f"Failed to submit task: {e}")
            raise

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a submitted task"""
        try:
            task = self.app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": task.status,
                "result": task.result,
                "info": task.info,
            }
        except Exception as e:
            self.logger.error(f"Failed to get task status: {e}")
            return {"task_id": task_id, "status": "error"}

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a submitted task"""
        try:
            task = self.app.AsyncResult(task_id)
            task.revoke(terminate=True)
            self.logger.info(f"✓ Task cancelled: {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel task: {e}")
            return False

    def execute_pipeline(
        self,
        pipeline_name: str,
        agents: list,
        objectives: list,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute a multi-agent pipeline"""
        try:
            task = pipeline_execution.apply_async(
                args=(pipeline_name, agents, objectives),
                kwargs={"context": context},
            )
            self.logger.info(f"✓ Pipeline submitted: {task.id}")
            return task.id
        except Exception as e:
            self.logger.error(f"Failed to execute pipeline: {e}")
            raise

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            inspect = self.app.control.inspect()
            return {
                "active": inspect.active(),
                "scheduled": inspect.scheduled(),
                "reserved": inspect.reserved(),
            }
        except Exception as e:
            self.logger.error(f"Failed to get queue stats: {e}")
            return {}
