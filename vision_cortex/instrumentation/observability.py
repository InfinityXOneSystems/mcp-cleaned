"""Observability helpers: simple in-memory metrics and logging helpers.

Replace with Prometheus/OpenTelemetry integrations in production.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, Any
import os
import json

_REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("CELERY_BROKER_URL")
_redis = None
if _REDIS_URL:
    try:
        import redis

        _redis = redis.from_url(_REDIS_URL, decode_responses=True)
    except Exception:
        _redis = None

logger = logging.getLogger(__name__)


class SimpleMetrics:
    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)

    def increment(self, key: str, value: int = 1) -> None:
        self._counters[key] += value

    def get(self, key: str) -> int:
        return self._counters.get(key, 0)

    def snapshot(self) -> Dict[str, int]:
        return dict(self._counters)


metrics = SimpleMetrics()

try:
    from prometheus_client import CollectorRegistry, Counter, generate_latest, CONTENT_TYPE_LATEST
    PROM_REGISTRY = CollectorRegistry()
    PROM_DISPATCH_QUICK = Counter('dispatch_quick_total', 'Quick dispatches', registry=PROM_REGISTRY)
    PROM_ENQUEUE_LONG = Counter('enqueue_long_total', 'Long task enqueues', registry=PROM_REGISTRY)
    PROM_TASK_LATENCY = None
    PROM_QUEUE_DEPTH = None
    try:
        from prometheus_client import Histogram, Gauge

        PROM_TASK_LATENCY = Histogram('task_latency_seconds', 'Long task latency seconds', registry=PROM_REGISTRY)
        PROM_QUEUE_DEPTH = Gauge('task_queue_depth', 'Task queue depth (approx)', registry=PROM_REGISTRY)
    except Exception:
        PROM_TASK_LATENCY = None
        PROM_QUEUE_DEPTH = None
except Exception:
    PROM_REGISTRY = None
    PROM_DISPATCH_QUICK = None
    PROM_ENQUEUE_LONG = None

# In-process task store for immediate tasks (task_id -> result/status)
def _redis_key(task_id: str) -> str:
    return f"vision_cortex:task:{task_id}"


def store_task(task_id: str, payload: Dict[str, Any]) -> None:
    """Store task payload in Redis if available, otherwise in-memory fallback."""
    if _redis:
        try:
            _redis.set(_redis_key(task_id), json.dumps(payload))
        except Exception:
            logger.exception("Failed to store task in Redis; falling back to in-memory")
            _INPROC_TASK_STORE[task_id] = payload
    else:
        _INPROC_TASK_STORE[task_id] = payload


def get_task(task_id: str) -> Dict[str, Any] | None:
    """Retrieve task payload from Redis or in-memory store."""
    if _redis:
        try:
            val = _redis.get(_redis_key(task_id))
            if val:
                return json.loads(val)
        except Exception:
            logger.exception("Failed to read task from Redis; checking in-memory store")
    return _INPROC_TASK_STORE.get(task_id)

# Keep in-memory store as fallback
_INPROC_TASK_STORE: Dict[str, Dict[str, Any]] = {}
