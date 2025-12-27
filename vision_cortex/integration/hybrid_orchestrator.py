"""Hybrid Orchestrator: bridges SmartRouter and AgentFactory.

Behaviors:
- Routes quick intents to SmartRouter (sync)
- Sends long-running tasks to AgentFactory for async execution (in-process queue by default)
- Optionally integrates with Celery if `USE_CELERY=true` and Celery is installed.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any, Dict, Optional

try:
    # AgentFactory from autonomy_stack
    from autonomy_stack.agent_factory import AgentFactory
except Exception:
    AgentFactory = None

from vision_cortex.integration.agent_integration import init_agents
from vision_cortex.comms.router import SmartRouter
from vision_cortex.agents.base_agent import AgentContext

from vision_cortex.instrumentation.observability import metrics, PROM_DISPATCH_QUICK, PROM_ENQUEUE_LONG, PROM_QUEUE_DEPTH, store_task
from vision_cortex.instrumentation import observability as obs

logger = logging.getLogger(__name__)


class InProcessQueue:
    def __init__(self):
        self._loop = asyncio.get_event_loop()

    async def enqueue(self, coro):
        return await coro


class HybridOrchestrator:
    def __init__(self, use_celery: bool = False):
        self.router: SmartRouter = init_agents()
        self.factory = AgentFactory() if AgentFactory else None
        self.use_celery = use_celery and os.environ.get("USE_CELERY", "false").lower() == "true"
        self._queue = None
        if self.use_celery:
            logger.info("HybridOrchestrator using Celery (configured via USE_CELERY)")
            # Celery integration placeholder - not auto-configured here
            self._queue = None
        else:
            self._queue = InProcessQueue()

    def dispatch_quick(self, intent: str, ctx: AgentContext, data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch using SmartRouter for quick, low-latency tasks."""
        metrics.increment("dispatch_quick_total")
        if PROM_DISPATCH_QUICK:
            PROM_DISPATCH_QUICK.inc()
        payload = {"context": ctx, "data": data}
        return self.router.dispatch(intent, payload)

    async def execute_long(self, role: str, objective: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute long-running task via AgentFactory (async).

        If AgentFactory is not available, raise.
        """
        metrics.increment("execute_long_total")
        if not self.factory:
            raise RuntimeError("AgentFactory unavailable; cannot execute long task")

        # execute via factory (async)
        result = await self.factory.execute_task(role, objective, context)
        # store or transform TaskResult into serializable dict
        return {
            "task_id": result.task_id,
            "status": str(result.status),
            "result": result.result,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }

    async def enqueue_long(self, role: str, objective: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enqueue a long-running task: uses Celery if configured, otherwise runs in-process."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        metrics.increment("enqueue_long_total")
        if PROM_ENQUEUE_LONG:
            PROM_ENQUEUE_LONG.inc()
        # Approximate queue depth increment
        try:
            if PROM_QUEUE_DEPTH and obs._redis:
                try:
                    obs._redis.incr("vision_cortex:queue_depth")
                    val = obs._redis.get("vision_cortex:queue_depth") or 0
                    PROM_QUEUE_DEPTH.set(int(val))
                except Exception:
                    logger.debug("Failed to increment Redis queue depth")
        except Exception:
            logger.debug("Queue depth metric update (enqueue) failed")
        if self.use_celery:
            try:
                from vision_cortex.integration.celery_app import execute_long_task
                # call Celery task asynchronously
                async_result = execute_long_task.delay(role, objective, context)
                return {"task_id": task_id, "status": "queued", "celery_id": async_result.id}
            except Exception as e:
                logger.exception("Failed to enqueue Celery task: %s", e)
                raise

        # In-process execution: run execute_long and return immediate task info
        result = await self.execute_long(role, objective, context)
        payload = {"task_id": task_id, "status": "completed", "result": result}
        try:
            store_task(task_id, payload)
        except Exception:
            logger.exception("Failed to store task result")
        # Update approximate queue depth (decrement)
        try:
            if PROM_QUEUE_DEPTH and obs._redis:
                try:
                    obs._redis.decr("vision_cortex:queue_depth")
                    val = obs._redis.get("vision_cortex:queue_depth") or 0
                    PROM_QUEUE_DEPTH.set(int(val))
                except Exception:
                    logger.debug("Failed to update Redis queue depth metric")
        except Exception:
            logger.debug("Queue depth metric update failed")
        return payload
