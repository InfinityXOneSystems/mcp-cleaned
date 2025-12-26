AUTONOMY SAFETY MODEL — POWERFUL AND BOUNDED

Allowed Unattended

- Read-only tools: discovery, search, schema publication, health checks, stats.
- Safe scrapers with strict allowlist and rate limits.
- Memory sync to Firestore with retry/backoff and dead-letter.
- Telemetry: status beacons, audit logs, drift monitors.

Explicit Gating Required

- Any write-capable tool (filesystem, repositories, cloud resources).
- Trading or financial operations (paper_trading.py and variants).
- Remote control commands; deployment actions; configuration changes.
- Actions schema re-import; tool registry changes.

Never Self-Execute

- Deployments, key rotations, destructive deletes, merges to protected branches, production memory migrations.

Forbidden During Demo Windows

- Write execution outside dry_run.
- Schema changes or adapter upgrades.
- Credential modifications.
- Actions re-import with different base URL.
- Tool registry mutations.

Escalation & Enforcement

- Severity tiers with automatic gates: warn → read-only → kill-switch.
- Auto-disable on error spike or auth failures; page operator.
- Admin API enforces toggles without blocking safe reads.
- Correlation IDs on all actions; audit logs linked to tenants.
