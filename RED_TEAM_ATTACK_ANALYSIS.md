RED-TEAM — IF I WERE ATTACKING THIS

- Key & Auth Bypass: Exploit optional header enforcement; guess static demo keys; use path drift (/mcp/executeMCPTool) to find unguarded handlers. Mitigation: mandatory auth, host allowlist, 401 on missing keys, schema lock.
- Schema Poisoning: Feed Actions a mismatched base URL or altered schema to route to unintended endpoints. Mitigation: signed schema with checksum; import gate; base URL pinning.
- Tool Abuse: Invoke high-cost tools repeatedly (DoS) or write-capable tools without dry_run. Mitigation: per-tool rate limits, budgets, dry_run_required, allowlist.
- Replay Attacks: Repeat the same request with timing to exhaust resources or duplicate actions. Mitigation: idempotency keys, short TTL dedup, request hashing.
- Port Contention Chaos: Bind to 8000 early; cause silent failures and operator confusion. Mitigation: preflight port checks; fail-fast with explicit error; random high ports in dev.
- Remote Control Misuse: Abuse command mappings in remote_control server to execute unsafe shell actions. Mitigation: strict allowed dict, token enforcement, audit logs, deny dangerous commands.
- Credential Harvesting: Scan repo and local machines for creds JSON; exfiltrate; impersonate. Mitigation: remove creds from repo; Secret Manager; WIF; rotate.
- Memory Corruption: Cause Firestore writes to fail silently; break agent loops; create data gaps. Mitigation: retry/backoff, dead-letter, integrity checks, alerts.
- Endpoint Enumeration: Mix localhost/127.0.0.1; alternate paths; find lenient handlers. Mitigation: host allowlist; route normalization; deny unknown paths.
- Health Spoofing: Respond 200 without component checks; hide failures. Mitigation: deterministic health contract with component status and checksum.
