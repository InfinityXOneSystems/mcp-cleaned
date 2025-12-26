# DEMO-SAFE OPERATIONS RUNBOOK — CANONICAL

This document freezes operational truth for safe, repeatable demos. It is documentation-only: no code changes, no refactors, no performance tuning. Use these checklists exactly as written.

---

## 1) GO / NO-GO DEMO CARD

- Purpose: Decide if a demo proceeds safely. Run in minutes.
- Scope: MCP adapter, gateway, schema, governance safety, Actions alignment.

### Preflight Checklist
- Free local demo port 8000 (if applicable):
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess |
  Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
```
- Start gateway (recommended local run):
```powershell
uvicorn omni_gateway:app --host 0.0.0.0 --port 8000
```
- Health and stats:
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/health).StatusCode
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/stats).Content
```
- Schema availability:
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/schema).StatusCode
```
- Tool discovery:
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/tools).Content
```
- Governance demo-safety (headers to use in demo):
  - Require authentication: set `MCP_ENABLE_AUTH=true` and provide `X-MCP-KEY`.
  - Enforce read-only: include `X-MCP-ReadOnly=true` in demo requests.
  - Prefer dry run for write-capable tools: add `dry_run=true`.

### Explicit GO Conditions
- `/mcp/health` returns 200 with sane payload.
- `/mcp/schema` returns 200 and is valid OpenAPI 3.0.
- `/mcp/tools` lists tools; count is non-zero and expected.
- Authentication enforced (`X-MCP-KEY`) for public demos.
- Read-only honored; write-capable tools executed with `dry_run=true`.
- Base URL used in demo matches the configured Actions base URL.

### Explicit NO-GO Triggers
- Any 4xx/5xx on `/mcp/health` or `/mcp/schema`.
- Authentication disabled for public demo exposure.
- Read-only not enforced; write operations permitted.
- Tool discovery empty or clearly mismatched with expected inventory.
- Actions base URL not aligned with demo URL (local vs. prod mismatch).

### Safe Demo Paths
- Use read-only mode globally via `X-MCP-ReadOnly=true`.
- Execute via named endpoints with `dry_run=true`.
- Limit demonstrations to read/list operations during public sessions.
- Keep cockpit browsing limited to non-sensitive views.

### Never-Demo-Live Paths
- Any CRITICAL/HIGH write operation (e.g., destructive Docker, cloud infra changes, repository writes).
- Tools requiring privileged credentials when those credentials are not confirmed.
- Anything involving external systems without explicit sandbox confirmation.

### Emergency Fallback Actions
- Stop process bound to port 8000; restart gateway:
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
Start-Sleep -Seconds 2
uvicorn omni_gateway:app --host 0.0.0.0 --port 8000
```
- Immediately switch demo to read-only and dry-run:
  - Add header `X-MCP-ReadOnly=true`.
  - Add query `dry_run=true`.
- If schema import is failing, revert Actions to last known-good schema and pause execution demos.

### Decision Logging Guidance
- Record GO/NO-GO decision, timestamp, operator, and base URL used.
- Store a brief summary of health, schema check, tools count, and governance mode in canonical memory/log.

---

## 2) ORCHESTRATOR AUTHORITY NOTE

- **Canonical Orchestrator:** `omni_gateway.py` is the authoritative entrypoint.
- **Legacy/Non-Authoritative:** `api_gateway.py` is legacy/secondary and not the primary execution surface.
- **Why `omni_gateway.py` is Canonical:** It mounts the MCP adapter router and serves cockpit/related interfaces; it is the gateway surface used for demos and Actions.
- **MCP Adapter Mount Path:** `/mcp/*`.
- **Correct Local Run Guidance:** Use `uvicorn omni_gateway:app --host 0.0.0.0 --port 8000` (ASGI server) rather than `python omni_gateway.py`.
- **Base URL Discipline:**
  - Demo: use the local or staging gateway base URL consistently (e.g., `http://localhost:8000/mcp`).
  - Production: use the public gateway base URL consistently (e.g., `https://<prod-host>/mcp`).
  - Do not mix local and production URLs within a single demo session.

---

## 3) CUSTOM GPT ACTIONS DRIFT CHECKLIST

- **When to Re-Import OpenAPI Schema:**
  - Any change to tool registry (add/remove/update tools or parameters).
  - Governance adjustments affecting access or behavior.
  - Adapter endpoint/schema changes.

- **Export and Validate Schema:**
```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/schema -OutFile mcp-openapi.json
```
```bash
# Validate with an OpenAPI 3.0 validator available to you
openapi validate mcp-openapi.json
```

- **Post-Import Sanity Tests:**
  - Call `GET /mcp/health`: expect 200 and healthy.
  - Call `GET /mcp/tools`: confirm non-zero tool count.
  - Execute a known-safe named endpoint with `dry_run=true`.
  - Confirm Actions base URL exactly matches the gateway URL used.

- **Common Drift Signals & Symptoms:**
  - Tool count mismatch between `/mcp/tools` and Actions.
  - New or removed endpoints not appearing in Actions.
  - Execution errors due to outdated parameter schemas.
  - Base URL mismatch causing HTTP failures.

- **Rollback Guidance:**
  - Retain last known-good `mcp-openapi.json`.
  - If drift causes failures, revert Actions to the last known-good schema and re-attempt later with validated changes.

---

## 4) CREDENTIAL HYGIENE CHECKLIST

- **Required Environment Variables:**
  - `MCP_ENABLE_AUTH` (enforce header auth in demos and production).
  - `MCP_API_KEY` (provide via environment; never inline in code or docs).
  - Any mandatory cloud project variables required by Firestore access.

- **Auth Enforcement Requirements:**
  - For public demos, require `X-MCP-KEY` header on execution requests.
  - Confirm auth in Actions configuration for imported operations.

- **Read-Only Defaults for Demos:**
  - Use `X-MCP-ReadOnly=true` across demo calls.
  - Prefer `dry_run=true` for write-capable paths.

- **Secrets Handling Rules (Never Inline):**
  - Service account JSON and API keys must not be committed.
  - Supply secrets through environment or secret managers only.

- **Google Cloud / Firestore Access Notes:**
  - In production, prefer Workload Identity; locally, set `GOOGLE_APPLICATION_CREDENTIALS` from a protected path only.
  - Ensure Firestore project configuration is present and valid before demos requiring persistence.

- **Rotation and Audit Reminders:**
  - Rotate `MCP_API_KEY` regularly.
  - Log request IDs, timings, and decisions for audit.

- **Public Exposure Cautions:**
  - Do not expose cockpit or `/mcp/*` unauthenticated.
  - If public access is necessary, enforce auth, read-only, and consider IP constraints.

- **Base URL Consistency Rules:**
  - Align Actions base URL with the demo gateway URL.
  - Avoid mixing local and production URLs during a session.

---

## 5) NIGHTLY AUDIT PLAYBOOK (DOCUMENTATION ONLY)

- **Purpose:** Automated confidence checks documented for nightly use.

### Health Endpoint Checks
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/health).Content
```

### Stats and Tool Registry Checks
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/stats).Content
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/tools).Content
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/categories).Content
```

### Schema Availability Verification
```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/schema -OutFile mcp-openapi.json
```
- Validate the downloaded schema using an OpenAPI 3.0 validator available to you.

### Governance Sanity Probe
- Attempt a write-capable operation in read-only mode; expect a block/safe response.
```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/execute/github_create_issue \
  -Method POST \
  -Headers @{ 'X-MCP-ReadOnly' = 'true'; 'Content-Type' = 'application/json' } \
  -Body '{ "owner": "demo", "repo": "demo", "title": "Demo" }'
```

### Firestore Connectivity Check (Optional Local)
```powershell
$p = 'C:\\Users\\JARVIS\\AppData\\Local\\InfinityXOne\\CredentialManager\\workspace-sa.json'
if (Test-Path $p) {
  $env:GOOGLE_APPLICATION_CREDENTIALS = $p
  $env:FIRESTORE_PROJECT = 'infinity-x-one-systems'
  python .\\inspect_firestore.py
}
```

### Adapter Verification
```powershell
python verify_mcp_adapter.py .
```

### What Constitutes a Red Flag
- Non-200 responses from `/mcp/health` or `/mcp/schema`.
- Empty or clearly incorrect tool registry in `/mcp/tools`.
- Schema invalid or import failures in Actions.
- Governance not blocking write-capable operations in read-only.
- Adapter verification script reports failures.

### Escalation Criteria and Logging Guidance
- If any red flag occurs, mark demo as NO-GO and log details: timestamp, base URL, failing checks, operator identity.
- Store the nightly audit results in canonical memory/log for traceability.

---

This runbook is canonical. Preserve velocity, protect demos, freeze reality.
# Demo-Safe Operations Runbook

This document consolidates demo-safe guidance for running the Infinity XOS system: GO/NO-GO decision card, orchestrator authority note, Custom GPT Actions drift checklist, credential hygiene checklist, and a nightly audit playbook. Documentation-only; no code changes.

---

## GO/NO-GO Demo Card

- **Purpose:** Fast decision gate to determine whether to proceed with a demo.
- **Scope:** MCP adapter surface, gateway health, schema availability, governance safety, and Actions readiness.

### Preflight Checks

- **Free the demo port (8000):**
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess |
  Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
```

- **Start the gateway (recommended local run):**
```powershell
uvicorn omni_gateway:app --host 0.0.0.0 --port 8000
```

- **Baseline health:**
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/health).StatusCode
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/stats).Content
```

- **Schema availability:**
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/schema).StatusCode
```

- **Tool discovery:**
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/tools).Content
```

- **Governance demo-safety:**
  - Ensure authentication in demos: set `MCP_ENABLE_AUTH=true` and provide `X-MCP-KEY`.
  - Default to read-only mode: set `X-MCP-ReadOnly=true` on demo requests.
  - Prefer `dry_run=true` for write-capable tools.

### GO Criteria

- **Health endpoints:** `/mcp/health` returns 200 and sane payload.
- **Schema:** `/mcp/schema` responds and is parseable as OpenAPI 3.0.
- **Discovery:** `/mcp/tools` lists tools; count aligns with expectations.
- **Security:** Authentication enforced (`X-MCP-KEY`), read-only honored.
- **Demo requests:** Write-capable tools use `dry_run=true` or are blocked by read-only.

### NO-GO Triggers

- 4xx/5xx on `/mcp/health` or `/mcp/schema`.
- Authentication disabled during public-facing demo.
- Read-only not enforced; write ops permitted.
- Tool discovery empty or mismatched without explanation.
- Base URL mismatch between the demo and Actions configuration.

### Record Decision

- Log GO/NO-GO outcome, base URL, and timestamp to canonical memory (Firestore) or a local audit trail.

---

## Orchestrator Authority Note

- **Canonical Entrypoint:** The authoritative orchestrator is [omni_gateway.py](omni_gateway.py).
- **MCP Surface:** MCP HTTP adapter is mounted in [omni_gateway.py](omni_gateway.py) under `/mcp/*`.
- **Legacy Surface:** [api_gateway.py](api_gateway.py) is legacy/secondary and not the primary execution surface.
- **Launch Guidance:** Prefer `uvicorn omni_gateway:app` for local runs to ensure proper ASGI serving and avoid script-bound limitations.
- **Base URL Discipline:** Point Custom GPT Actions to the gateway’s `/mcp` base (e.g., `https://<host>/mcp`). Avoid mixing local (`http://localhost:8000`) and production URLs in the same demo.

---

## Custom GPT Actions Drift Checklist

- **When to Re-Import:**
  - Tool registry changes (add/remove/modify tools or parameters).
  - Governance changes that affect accessible operations.
  - Adapter schema changes or endpoint path adjustments.

- **Export the Latest Schema:**
```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/schema -OutFile mcp-openapi.json
```

- **Validate the Schema (any OpenAPI 3.0 validator):**
```bash
openapi validate mcp-openapi.json
# Or use an equivalent validator in your environment
```

- **Re-Import to Custom GPT Actions:**
  - Upload `mcp-openapi.json` into Actions.
  - Configure header auth: `X-MCP-KEY`.
  - Confirm the base URL matches the gateway’s public URL (not localhost).

- **Sanity Test Post-Import:**
  - Call `GET /mcp/health` and `GET /mcp/tools`.
  - Execute a known safe tool via named endpoint with `dry_run=true`.

- **Drift Detection Signals:**
  - Tool count discrepancy: `/mcp/tools` count vs. Actions-visible operations.
  - OpenAPI changes not reflected in Actions (missing or stale endpoints).
  - Base URL mismatch causing failed calls.

- **Rollback:**
  - Keep last-known-good schema; revert if issues are detected.

---

## Credential Hygiene Checklist

- **Secrets in Repo:**
  - No service account JSON or API keys are committed. Use environment variables only.

- **Authentication Enforcement:**
  - Set `MCP_ENABLE_AUTH=true` in demos and production.
  - Provide `MCP_API_KEY` via environment (not hard-coded).

- **Read-Only Defaults:**
  - Use `X-MCP-ReadOnly=true` header during demos; prefer `dry_run=true` for write-capable tools.

- **Google Cloud Access:**
  - Use Workload Identity in production; locally set `GOOGLE_APPLICATION_CREDENTIALS` from a protected path only.
  - Ensure the Firestore project/env is correctly set and validated.

- **Least Privilege:**
  - Restrict service account scopes/roles to Firestore and logging as needed.

- **Rotation & Audit:**
  - Rotate `MCP_API_KEY` regularly; log request IDs and timings.
  - Monitor `/mcp/stats` and Firestore entries for unusual activity.

- **Public Exposure:**
  - Do not expose cockpit or `/mcp/*` endpoints unauthenticated in public demos.
  - If public access is necessary, enforce auth + read-only and consider IP restrictions.

- **Base URL Consistency:**
  - Align Actions base URL with the gateway URL used in the demo.

---

## Nightly Audit Playbook

- **Purpose:** Automated operational confidence checks; documentation-only sequence for a nightly run.

### Steps

1. **Clear Port (Optional Local):**
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess |
  Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
```

2. **Service Availability:**
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/health).Content
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/stats).Content
```

3. **Tools & Categories Sanity:**
```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/tools).Content
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/categories).Content
```

4. **Schema Consistency:**
```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/schema -OutFile mcp-openapi.json
```
- Validate the downloaded schema using an OpenAPI validator available in your environment.

5. **Governance Safety Probe:**
- Attempt a write-capable operation in read-only mode and expect a block or safe response.
```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/mcp/execute/github_create_issue \
  -Method POST \
  -Headers @{ 'X-MCP-ReadOnly' = 'true'; 'Content-Type' = 'application/json' } \
  -Body '{ "owner": "demo", "repo": "demo", "title": "Demo" }'
```

6. **Firestore Connectivity (Optional Local):**
- Ensure credentials are available and run the inspection utility.
```powershell
$p = 'C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager\workspace-sa.json'
if (Test-Path $p) {
  $env:GOOGLE_APPLICATION_CREDENTIALS = $p
  $env:FIRESTORE_PROJECT = 'infinity-x-one-systems'
  python .\inspect_firestore.py
}
```

7. **Adapter Verification Script:**
```powershell
python verify_mcp_adapter.py .
```

### Output & Escalation

- **Record:** Store results (health, stats, tools count, schema check, governance probe outcome, verification script summary) in canonical memory or a nightly audit log.
- **Escalate:** If any check fails (non-200 on health/schema, schema invalid, governance not enforced, adapter verification fails), flag as NO-GO for demos and investigate.

---

## References

- Adapter Guide: [MCP_HTTP_ADAPTER_GUIDE.md](MCP_HTTP_ADAPTER_GUIDE.md)
- Testing Guide: [MCP_ADAPTER_TESTING_GUIDE.md](MCP_ADAPTER_TESTING_GUIDE.md)
- Quick Reference: [MCP_QUICK_REFERENCE.md](MCP_QUICK_REFERENCE.md)
- Implementation Summary: [MCP_ADAPTER_IMPLEMENTATION_SUMMARY.md](MCP_ADAPTER_IMPLEMENTATION_SUMMARY.md)
- Delivery Checklist: [MCP_DELIVERY_CHECKLIST.md](MCP_DELIVERY_CHECKLIST.md)
