# Agents — Capability Layer (Operator Guide)

This README describes how to implement capability-expanding agents that cooperate through Firestore memory and task contracts. Do not modify enforcement, auth, demo-mode or entrypoints.

## Roles (quick map)
- Scout: discover sources and signals; output structured artifacts.
- Architect: decompose objectives into task graphs and assign roles.
- Executor: run deterministic tools and transformations; produce artifacts.
- Predictor: generate predictions, confidence bands, and scores.
- Memory: curate, compact, index, and rehydrate state across sessions.

## Run Model
- Agents run via `python -m agents.runner --start` per repo patterns.
- Cooperative async loops; emit `agent_status` to `mcp_memory` every 10–30s.
- Use idempotency keys to avoid duplicate work.

## Contracts (must-follow)
- Task object and handoff envelope per [AGENT_ARCHITECTURE.md](../AGENT_ARCHITECTURE.md).
- Persist only to documented collections (`agent_tasks`, `agent_runs`, `agent_mailbox`, and existing `mcp_memory`).
- Include `session_hash` on all writes. Use merge writes (backward compatible).

## Status Emission (existing convention)
Write to `mcp_memory` with `type: agent_status`:
```json
{
  "session_hash": "hash",
  "type": "agent_status",
  "agent_id": "executor-1",
  "role": "executor",
  "status": "running",
  "message": "processing 15 urls",
  "created_at": "ISO"
}
```

## Implementing a New Agent
- Expose `async def run(cfg)`; never block indefinitely; small work units; periodic yields.
- Read tasks from `agent_tasks` filtered by role and priority; claim with a lease (see architecture spec).
- Emit `agent_runs` records with `events[]` and `artifacts[]`.

## Safety Boundaries
- Do not modify rate limits, auth checks, demo-mode, or secrets handling.
- Demo-safe mode implies read-only outputs and conservative writes (size, PII redaction if required by auditor).

## Debugging
- Use `agent_runs.events` for replay and checkpoints.
- Prefer structured logs; keep sensitive data out of logs by default.
