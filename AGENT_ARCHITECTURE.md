# Agent Architecture and Contracts (Future-State)

Purpose: expand capability surface safely. No changes to enforcement, entrypoints, demo-mode, or secrets. This document defines agent roles, contracts, task handoffs, runtime model, and Firestore schemas (docs-only) that auditors can harden and builders can implement without rework.

## Agent Taxonomy (Roles)
- Scout: discovery and acquisition. Finds signals, sources, and seed opportunities; produces structured artifacts (links, docs, extractions).
- Architect: planning and decomposition. Converts objectives into task graphs and assigns to specialized agents.
- Executor: deterministic action-taker. Runs tools, transforms data, writes outputs; never changes auth or controls.
- Predictor: modeling and scoring. Produces predictions, confidence bands, and lead scores from features.
- Memory: state and context librarian. Curates, compacts, indexes, and rehydrates memory across sessions.

## Responsibility Contracts
- Inputs: `objective`, `context`, `constraints`, `deadline`, `priority`, `session_hash`, optional `attachments`.
- Outputs: `status`, `artifacts[]`, `insights[]`, `events[]`, `confidence`, `next_recommended_actions[]`.
- Side effects: Firestore writes to documented collections only; conform to idempotency and immutability rules below.

## Task Object (Logical Contract)
```json
{
  "task_id": "uuid",
  "parent_task_id": null,
  "created_by": "architect|system|operator",
  "assigned_to": "scout|executor|predictor|memory|architect",
  "objective": "Find distressed SMB leads in TX energy",
  "context": {"industry_tags": ["energy","smb"], "time_horizon_days": 30},
  "constraints": {"demo_safe": true, "read_only": true},
  "priority": 7,
  "deadline": "2025-12-31T23:59:59Z",
  "handoff_reason": "Needs crawling and extraction",
  "expected_outcome": "Top 25 prospects with signals",
  "idempotency_key": "hash(objective+context)",
  "status": "queued|in_progress|blocked|done|canceled",
  "created_at": "ISO",
  "updated_at": "ISO"
}
```

## Agent-to-Agent Handoff Envelope
```json
{
  "envelope_id": "uuid",
  "task": {"task_id": "uuid", "assigned_to": "executor"},
  "session_hash": "hash",
  "artifacts": [{"type": "url_list", "value": ["https://..."]}],
  "signals": [{"name": "negative_cashflow_rumor", "strength": 0.62}],
  "attachments": [{"name": "seed.csv", "mime": "text/csv", "uri": "gs://..."}],
  "notes": "Focus on regulatory filings and layoffs",
  "security_context": {"mode": "demo_safe"},
  "trace": {"chain_id": "uuid", "step": 3}
}
```

## Background Execution Model (Non-Enforcing)
- Loop semantics: cooperative async loops with small sleeps, bounded work units, and periodic yielding.
- Heartbeat: each agent writes an `agent_status` memory doc every 10–30s while active.
- Backpressure: agents must respect queue depth hints and use `priority` + `deadline` for scheduling (no enforcement).
- Idempotency: every run emits an `agent_runs` record with `idempotency_key`. Duplicate keys imply safe no-op or merge.
- Crash safety: on startup, agent attempts resume (see below) with lease-based recovery.

## Firestore Schemas (Docs Only)
Do not change existing `mcp_memory` semantics. New collections are additive and optional. Builders must use merge writes.

### Collection: `agent_tasks`
- Key: `task_id`
- Fields:
  - `session_hash` (string)
  - `created_by` (string: `architect|system|operator`)
  - `assigned_to` (string role)
  - `objective` (string)
  - `context` (object)
  - `constraints` (object)
  - `priority` (int 1–10)
  - `deadline` (timestamp)
  - `status` (string)
  - `lease` (object: `{owner_agent_id, expires_at}`) — optional resume token
  - `idempotency_key` (string)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)

### Collection: `agent_runs`
- Key: `run_id`
- Fields:
  - `agent_id` (string)
  - `role` (string)
  - `task_id` (string)
  - `session_hash` (string)
  - `status` (string: `started|progress|completed|error|timeout`)
  - `progress` (number 0–1)
  - `events` (array of `{ts,type,payload}`)
  - `artifacts` (array of refs/URIs)
  - `idempotency_key` (string)
  - `started_at` (timestamp)
  - `ended_at` (timestamp)

### Collection: `agent_mailbox`
- Key: `message_id`
- Fields:
  - `to_agent_id` (string)
  - `from_agent_id` (string)
  - `session_hash` (string)
  - `task_id` (string)
  - `payload` (object) — handoff envelope
  - `status` (string: `new|read|claimed`)
  - `created_at` (timestamp)

### Existing: `mcp_memory` (Augmentation Guidance)
- Continue writing `type: agent_status` with fields:
  - `agent_id`, `role`, `session_hash`, `status`, `message`, `cpu`, `mem`, `queue_hints`, `created_at`.
  - Backward compatible; auditors can enforce rate limits and size caps.

## Restart / Resume Semantics
- Lease: when an agent claims a task, set `agent_tasks.lease = {owner_agent_id, expires_at}`. Expired leases are reclaimable.
- Idempotency: recompute `idempotency_key` from `objective+context` and compare against last `agent_runs` to avoid rework.
- Replay: use `agent_runs.events` to reconstruct last checkpoint; store `checkpoint_uri` in `agent_tasks` when available.
- Recovery: on boot, attempt to reclaim tasks with `status=in_progress` and expired leases owned by this agent class.

## Implementation Hooks (Builder Notes)
- Agents expose `async def run(cfg)` and never block indefinitely; persist `agent_status` per repo conventions.
- All writes must use `merge=True` and include `session_hash` for traceability.
- Never change auth, rate limits, or secrets—this document defines contracts, not enforcement.
