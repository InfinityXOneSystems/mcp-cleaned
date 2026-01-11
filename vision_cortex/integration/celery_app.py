"""Celery app configuration and tasks for Vision Cortex hybrid orchestrator.

Requires environment variables:
- CELERY_BROKER_URL (e.g. redis://localhost:6379/0)
- CELERY_BACKEND_URL (optional)
"""

from __future__ import annotations

import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)

BROKER = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND = os.environ.get("CELERY_BACKEND_URL", BROKER)

celery_app = Celery("vision_cortex_tasks", broker=BROKER, backend=BACKEND)


@celery_app.task(bind=True)
def execute_long_task(self, role: str, objective: str, context: dict | None = None):
    """Celery task wrapper that uses AgentFactory to execute a long-running task.

    This task imports `autonomy_stack.agent_factory` at runtime to avoid import
    errors in environments where the package isn't installed.
    """
    try:
        from autonomy_stack.agent_factory import AgentFactory
    except Exception as e:
        logger.exception("AgentFactory import failed in Celery worker: %s", e)
        raise

    factory = AgentFactory()
    # AgentFactory.execute_task is async; we need to run it in event loop
    try:
        import asyncio

        async def _run():
            return await factory.execute_task(role, objective, context)

        result = asyncio.get_event_loop().run_until_complete(_run())
        # Convert TaskResult to serializable dict if needed
        return {
            "task_id": result.task_id,
            "status": str(result.status),
            "result": result.result,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }
    except Exception:
        logger.exception("Long task execution failed in Celery worker")
        raise
