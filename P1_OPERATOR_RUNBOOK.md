P1 OPERATOR RUNBOOK — MANDATORY PROCEDURES

AUTHORITY
This runbook is the canonical operational truth for P1-hardened systems.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1 — LOCAL STARTUP (DEVELOPMENT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1.1 Preflight

```powershell
# Set credentials
$env:GOOGLE_APPLICATION_CREDENTIALS="$env:APPDATA\InfinityXOne\CredentialManager\workspace-sa.json"
$env:FIRESTORE_PROJECT="infinity-x-one-systems"
$env:MCP_API_KEY="<rotate-key-here>"

# Optional: Enable demo mode
$env:DEMO_MODE="1"

# Verify P1 enforcement
python p1_verify.py
```

Expected: All checks pass.

1.2 Start Gateway

```powershell
uvicorn omni_gateway_p1:app --host 127.0.0.1 --port 8000 --reload
```

Never use:
```powershell
python omni_gateway_p1.py  # ❌ REFUSED by P1
```

1.3 Health Check

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health | ConvertFrom-Json | ConvertTo-Json
```

Expected:
```json
{
  "status": "healthy",
  "components": {
    "gateway": "healthy",
    "adapter": "healthy",
    "firestore": "healthy"
  },
  "demo_mode": true,
  "version": "3.1-p1"
}
```

If any component shows "degraded" or "unavailable", STOP and debug.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2 — DEMO MODE ENFORCEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2.1 Activate Demo Mode

```powershell
$env:DEMO_MODE="1"
uvicorn omni_gateway_p1:app --host 127.0.0.1 --port 8000
```

2.2 Verify Demo Mode Active

```powershell
$headers = @{ "X-MCP-KEY" = $env:MCP_API_KEY }
$body = @{
    tool_name = "github_search_code"
    arguments = @{ query = "test"; max_results = 1 }
    dry_run = $false
} | ConvertTo-Json

Invoke-WebRequest `
    -Uri http://127.0.0.1:8000/mcp/execute `
    -Method POST `
    -Headers $headers `
    -Body $body `
    -ContentType "application/json" | ConvertFrom-Json
```

Expected:
```json
{
  "success": true,
  "demo_mode": true,
  "result": { "schema": [...] }
}
```

Even though `dry_run=$false`, demo mode forces dry_run=true.

2.3 Demo Mode GO/NO-GO

Before any demo with investors, partners, or press:
- [ ] DEMO_MODE=1 confirmed via /health
- [ ] X-MCP-KEY rotated (not default)
- [ ] All execute requests return demo_mode: true
- [ ] No write operations execute (verified in logs)
- [ ] Firestore writes succeed (test memory persistence)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3 — AUTH ENFORCEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3.1 Test Auth Required

Without X-MCP-KEY header:
```powershell
$body = @{ tool_name = "github_search_code"; arguments = @{} } | ConvertTo-Json
Invoke-WebRequest `
    -Uri http://127.0.0.1:8000/mcp/execute `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

Expected: HTTP 401
```json
{
  "success": false,
  "code": "AUTH_MISSING",
  "reason": "X-MCP-KEY header required",
  "correlationId": "<uuid>",
  "guidance": "Include X-MCP-KEY header with valid key"
}
```

3.2 Test Invalid Key

With wrong key:
```powershell
$headers = @{ "X-MCP-KEY" = "wrong-key" }
$body = @{ tool_name = "github_search_code"; arguments = @{} } | ConvertTo-Json
Invoke-WebRequest `
    -Uri http://127.0.0.1:8000/mcp/execute `
    -Method POST `
    -Headers $headers `
    -Body $body `
    -ContentType "application/json"
```

Expected: HTTP 401
```json
{
  "success": false,
  "code": "AUTH_INVALID",
  "reason": "X-MCP-KEY header invalid"
}
```

3.3 Rotate API Key

Before demos:
```powershell
$newKey = "DEMO-$(Get-Date -Format 'yyyyMMdd')-$(New-Guid | Select-Object -First 8)"
$env:MCP_API_KEY = $newKey
Write-Host "New key: $newKey"

# Restart gateway
uvicorn omni_gateway_p1:app --host 127.0.0.1 --port 8000
```

Document key in secure location (1Password, Secret Manager).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4 — KILL SWITCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4.1 Activate Kill Switch

If system is under attack or misbehaving:
```powershell
$env:KILL_SWITCH="1"
# Restart gateway
uvicorn omni_gateway_p1:app --host 127.0.0.1 --port 8000
```

4.2 Verify Kill Switch Active

```powershell
$headers = @{ "X-MCP-KEY" = $env:MCP_API_KEY }
$body = @{ tool_name = "github_search_code"; arguments = @{} } | ConvertTo-Json
Invoke-WebRequest `
    -Uri http://127.0.0.1:8000/mcp/execute `
    -Method POST `
    -Headers $headers `
    -Body $body `
    -ContentType "application/json"
```

Expected: HTTP 503
```json
{
  "success": false,
  "code": "KILL_SWITCH_ACTIVE",
  "reason": "Execution disabled by kill switch",
  "guidance": "Contact operator to restore service"
}
```

4.3 Deactivate Kill Switch

After incident resolved:
```powershell
$env:KILL_SWITCH="0"
# Restart gateway
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5 — NIGHTLY AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5.1 Health Probe

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health | ConvertFrom-Json
```

Check:
- [ ] status: "healthy"
- [ ] adapter: "healthy"
- [ ] firestore: "healthy"

5.2 Registry Integrity

```powershell
Invoke-WebRequest http://127.0.0.1:8000/mcp/stats | ConvertFrom-Json
```

Verify:
- [ ] tool_count matches expected (~59)
- [ ] registry_hash unchanged from last audit
- [ ] demo_mode reflects environment

5.3 Verify P1 Enforcement

```powershell
python p1_verify.py
```

Expected: All checks pass.

5.4 Check Logs for Anomalies

```powershell
# Check for auth failures
Select-String -Path .\logs\*.log -Pattern "P1: Auth failed"

# Check for kill switch activations
Select-String -Path .\logs\*.log -Pattern "KILL_SWITCH_ACTIVE"

# Check for execution failures
Select-String -Path .\logs\*.log -Pattern "P1: Failed tool="
```

Red flags:
- Repeated auth failures from same IP
- Kill switch activated without operator action
- Execution failures exceeding baseline

5.5 Rotate Keys

```powershell
# Every 30 days minimum
$env:MCP_API_KEY = "PROD-$(Get-Date -Format 'yyyyMMdd')-$(New-Guid)"
# Update Secret Manager
# Restart gateway
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6 — CLOUD RUN DEPLOYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6.1 Build and Deploy

```powershell
gcloud builds submit --config cloudbuild.yaml
```

6.2 Set Environment Variables

```bash
gcloud run services update omni-gateway \
  --set-env-vars DEMO_MODE=1,FIRESTORE_PROJECT=infinity-x-one-systems,MCP_API_KEY=<secret> \
  --region us-east1
```

Better: Use Secret Manager
```bash
gcloud run services update omni-gateway \
  --set-secrets MCP_API_KEY=MCP_API_KEY:latest \
  --region us-east1
```

6.3 Verify Cloud Run Health

```bash
curl https://omni-gateway-<hash>-<region>.run.app/health | jq .
```

6.4 Cloud Run GO/NO-GO

- [ ] Health returns 200
- [ ] Components all "healthy"
- [ ] demo_mode reflects intention
- [ ] Auth enforced (test without X-MCP-KEY)
- [ ] Logs show no errors in startup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 7 — ROLLBACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If P1 enforcement causes issues:

7.1 Revert to Previous Gateway

```powershell
git checkout <previous-commit>
uvicorn omni_gateway:app --host 127.0.0.1 --port 8000
```

7.2 Disable P1 Features Selectively

Not recommended, but if necessary:
```powershell
$env:DEMO_MODE="0"
$env:KILL_SWITCH="0"
```

7.3 Escalation

If rollback fails:
1. Activate kill switch (all execution stops)
2. Check FINAL_VERDICT.md for conditions
3. Contact system architect
4. Document incident in INCIDENT_LOG.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- This runbook is canonical for P1 operations
- All procedures are mandatory for demos and production
- Deviations require explicit authorization
- Report all anomalies immediately
- Update runbook when P1 enforcement changes
