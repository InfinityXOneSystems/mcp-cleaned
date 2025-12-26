FINAL VERDICT — SHIP/HOLD WITH CONDITIONS

- Production: HOLD. Gaps in auth, secrets, health contracts, drift protection, and resilience make production unsafe.
- Controlled Demo: SHIP ONLY UNDER P1 ENFORCEMENT.

MANDATORY DEMO CONDITIONS (NO EXCEPTIONS)

- Serve omni_gateway.py via uvicorn only; single base URL; host allowlist.
- Require X-MCP-KEY for all MCP endpoints; set DEMO_MODE=1 → enforce read-only and dry_run for any write-capable tool.
- Publish deterministic /health and /mcp/health with adapter, Firestore, registry hash, schema checksum.
- Lock Actions schema and base URL; re-import only if checksum matches; no endpoint changes during demo.
- Remove local creds from runtime; use WIF or ephemeral demo-only key injected via env; rotate post-demo.
- Enable per-tool rate limits and execution budgets; kill switch toggles prepared.
- Log requests with correlationId and session_hash; monitor dashboard for drift or failures; page operator on error spike.

Exit Criteria for Production

- P1 complete and verified (auth-on-by-default, secrets vault, health contracts, fences, error contracts, audit logging).
- P2 roadmap in execution: control/data/execution/audit planes established; HA; canary; multi-tenant boundaries.
