HARDENING PLAN — P1 (72H) / P2 (14–30D)

P1 — Immediate (72 hours)

- Canonical Authority Enforcement: Serve omni_gateway.py only via uvicorn; refuse direct python entrypoints; enforce single base path; host allowlist; strict routing.
- Deterministic Health Contracts: Implement /health, /api/status, /mcp/health returning 200 with component checks (adapter, Firestore, tool registry count/hash, OpenAPI checksum).
- Safe-Fail Defaults: Read-only default; dry-run default for any write-capable tool; deny execution when auth missing; DEMO_MODE=1 enforces X-MCP-READONLY=true.
- Auth-On-By-Default: Require X-MCP-KEY for all MCP endpoints; integrate Cloud Run IAM or OAuth for non-demo; remove static demo keys from code; rotate keys; host allowlist and TLS-only.
- Secrets Vault Discipline: Move secrets to GCP Secret Manager; remove JSON creds from repo; use Workload Identity; forbid local ad hoc mounts in prod.
- Blast-Radius Containment: Classify tools by side-effect; enforce per-tool allowlist; max_results caps; timeouts; per-tool rate limits; execution budgets.
- Circuit Breakers & Kill Switches: Global KILL_SWITCH env; per-category kill toggles; auto-disable on error rates; degrade to read-only.
- Schema Versioning & Locking: Lock OpenAPI version; embed schema_version; publish signed checksum; reject Actions imports on mismatch.
- Replay & Abuse Protection: Require idempotency key; throttle repeated requests; audit logs with request hash; refuse duplicates within TTL.
- Tool Execution Fencing: Strict Pydantic validation; sandbox execution; explicit allow_write flags; dry_run_required for write tools.
- Error Contracts: Structured JSON with code, reason, correlationId, guidance. Never emit 500 without body.
- Audit-First Logging: Structured logs with session_hash, request_id, tool_name, governance decisions; ship to GCP Logging; redact PII.
- Port Hygiene: Preflight port check; single listener policy; fail-fast with explicit error if occupied; backoff-retry for bind.
- Operator Playbooks: GO/NO-GO checklist; immutable demo mode steps; base URL discipline; Actions re-import procedure.

P2 — Near-Term (14–30 days)

- Control Plane: Admin API to manage governance toggles, tenants, tool allowlists, quotas; persisted config; SLOs/SLAs.
- Data Plane: Firestore with retry/backoff, dead-letter queue, integrity checks, encryption at rest, retention policies, partitioning.
- Execution Plane: Worker pool isolation, durable job queue, per-tool containers, egress limits, concurrency caps.
- Audit Plane: Dashboards, alerts, drift detection (schema diff, registry hash), daily audit automation, incident runbooks.
- Platformization: Multi-tenant boundaries, partner-specific keys, per-tenant quotas, per-tenant logs, regulatory audit exports.
- Resilience: HA gateway (replicas), canary deployments, blue/green schema rollout, graceful shutdown hooks.
