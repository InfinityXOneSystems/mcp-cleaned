Vision Cortex Hybrid Orchestrator
================================

This scaffold provides a hybrid pattern combining `SmartRouter` (quick intent routing)
and `AgentFactory` (production-grade agent lifecycle). It includes:

- `vision_cortex/integration/hybrid_orchestrator.py`: orchestrator that routes quick intents to `SmartRouter` and executes long-running work via `AgentFactory`.
- `vision_cortex/instrumentation/observability.py`: simple in-memory metrics helper (replace with Prometheus in production).
- `vision_cortex/integration/agent_integration.py`: bootstraps a default set of premade agents and maps common intents.
- `scripts/migrate_agents_to_factory.py`: helper to migrate existing router-registered agents into `AgentFactory` instances.
- `tests/smoke_chat_test.py`: smoke test for local dispatch to `CrawlerAgent`.

Quick start (dev)
------------------
1. Create a virtualenv and install requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the smoke test:

```powershell
python tests/smoke_chat_test.py
```

3. Start the gateway (dev):

```powershell
uvicorn omni_gateway:app --reload --host 0.0.0.0 --port 8000
```

4. POST to `/api/chat` with JSON {
   "intent": "discover",
   "session_id": "s1",
   "data": { "seed": { "sources": [ ... ] } }
}

Enabling Celery (optional)
---------------------------
- Configure `CELERY_BROKER_URL` and `CELERY_BACKEND_URL` environment variables.
- Set `USE_CELERY=true` and implement a Celery task wrapper that calls `HybridOrchestrator.execute_long`.
- Run Celery workers separately and point the orchestrator's `enqueue_long` to push tasks to Celery.

Next steps
----------
- Replace `SimpleBus` with a real message bus (Pub/Sub/Kafka) for production scale.
- Add Prometheus instrumentation and OpenTelemetry traces in `instrumentation`.
- Harden governance checks before allowing `enqueue_long` for privileged ops.

Observability & security
------------------------
- Metrics: optional Prometheus metrics are exposed at `/metrics` when `prometheus_client` is installed. The scaffold increments counters for quick dispatch and long task enqueues.
- Tracing: the repo includes OpenTelemetry dependencies in `requirements.txt`. Initialize tracing in the gateway to capture request spans and agent execution (we can add an init function if you want).
- API key: enable `ADMIN_API_KEY` environment variable to require `X-API-KEY` header for `/api/agents/enqueue`.
- Task status: for in-process tasks the endpoint `/api/agents/status/{task_id}` will return stored results. When using Celery, query Celery backend for task status.
