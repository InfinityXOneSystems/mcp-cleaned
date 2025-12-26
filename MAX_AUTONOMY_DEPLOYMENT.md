# MAX AUTONOMY DEPLOYMENT GUIDE
## Infinity X One Omni Gateway - Full Autonomous System

### Overview
This deployment enables maximum autonomy with:
- **Credential Gateway**: Secure read-only access to all secrets
- **Autonomous Orchestrator**: Background agents and triggers
- **Intelligence Endpoints**: Auto-learning arrival, mirror, pipeline
- **MCP Tools**: 59 tools with governance
- **Firestore Memory**: Persistent state and audit logs
- **Cloud Scheduler**: Automated triggers

---

## Security Model

### ✅ SAFE TO DEPLOY
The credential gateway is designed for **safe autonomous operation**:

1. **Read-only by default**: No API endpoints write secrets
2. **Source of truth**: Secret Manager (not exposed via API)
3. **Audit logging**: All accesses logged to Firestore
4. **Token-based auth**: Requires `X-Credential-Token` header
5. **Masked mode**: Can return masked credentials for display
6. **Governance**: Critical operations require approval

### Key Safety Features
- Credentials never logged in plaintext
- All access tracked with hash + timestamp
- Can inject into environment without exposure
- Works with Workload Identity (no keys in container)

---

## Quick Deploy (Production)

### 1. Set up secrets in Secret Manager
```bash
# Your secrets should already exist:
# - mcp-api-key
# - workspace-sa-json
# - github-app-config
# - github-app-private-key
# - firebase-config
# - gemini-api-key
# - openai-api-key
# - hostinger-api-key

# Verify secrets exist
gcloud secrets list --project=infinity-x-one-systems
```

### 2. Create service account (if not exists)
```bash
gcloud iam service-accounts create mcp-gateway-sa \
  --display-name="MCP Gateway Service Account" \
  --project=infinity-x-one-systems

# Grant necessary permissions
gcloud projects add-iam-policy-binding infinity-x-one-systems \
  --member="serviceAccount:mcp-gateway-sa@infinity-x-one-systems.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding infinity-x-one-systems \
  --member="serviceAccount:mcp-gateway-sa@infinity-x-one-systems.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding infinity-x-one-systems \
  --member="serviceAccount:mcp-gateway-sa@infinity-x-one-systems.iam.gserviceaccount.com" \
  --role="roles/cloudscheduler.admin"
```

### 3. Deploy to Cloud Run
```bash
cd c:\AI\repos\mcp

# Submit build
gcloud builds submit --config cloudbuild.yaml --project=infinity-x-one-systems

# Build deploys automatically to Cloud Run with:
# - Firestore enabled
# - Secret Manager access
# - Workload Identity
# - Min 1 instance (always on)
# - 2GB RAM, 2 CPUs
# - 1 hour timeout
```

### 4. Set up Cloud Scheduler triggers
```bash
# Set token in env
export CREDENTIAL_GATEWAY_TOKEN=$(gcloud secrets versions access latest --secret=mcp-api-key --project=infinity-x-one-systems)

# Deploy scheduler jobs
bash deploy_scheduler.sh
```

### 5. Verify deployment
```bash
# Get service URL
export GATEWAY_URL=$(gcloud run services describe gateway --region=us-east1 --project=infinity-x-one-systems --format='value(status.url)')

echo "Gateway URL: $GATEWAY_URL"

# Test health
curl $GATEWAY_URL/health

# Test credential gateway
curl $GATEWAY_URL/credentials/health

# Test autonomy
curl $GATEWAY_URL/autonomy/health

# Test MCP tools
curl $GATEWAY_URL/mcp/listMCPTools
```

---

## Local Development

### Start gateway with all features
```powershell
# Set environment
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager\workspace-sa.json"
$env:FIRESTORE_PROJECT="infinity-x-one-systems"
$env:FIRESTORE_COLLECTION="mcp_memory"
$env:MCP_API_KEY="INVESTORS-DEMO-KEY-2025"
$env:CREDENTIAL_GATEWAY_TOKEN="INVESTORS-DEMO-KEY-2025"
$env:SAFE_MODE="true"
$env:DEV_MODE="true"  # Relaxes some auth for local dev

# Start gateway
python -m uvicorn omni_gateway:app --host 0.0.0.0 --port 8000 --reload
```

### Test credential gateway locally
```powershell
# List available credential types
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/credentials/list -Headers @{'X-Credential-Token'='INVESTORS-DEMO-KEY-2025'}).Content | ConvertFrom-Json

# Get credentials (masked)
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/credentials/get -Method POST `
  -Body (@{ credential_type='openai'; key='api_key'; masked=$true } | ConvertTo-Json) `
  -ContentType 'application/json' `
  -Headers @{'X-Credential-Token'='INVESTORS-DEMO-KEY-2025'}).Content | ConvertFrom-Json

# Inject credentials into environment
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/credentials/inject -Method POST `
  -Body (@{ credential_type='openai' } | ConvertTo-Json) `
  -ContentType 'application/json' `
  -Headers @{'X-Credential-Token'='INVESTORS-DEMO-KEY-2025'}).Content | ConvertFrom-Json

# Check audit log
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/credentials/audit -Headers @{'X-Credential-Token'='INVESTORS-DEMO-KEY-2025'}).Content | ConvertFrom-Json
```

### Test autonomous agents locally
```powershell
# Get capabilities
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/autonomy/capabilities).Content | ConvertFrom-Json

# Start an agent
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/autonomy/agents/start -Method POST `
  -Body (@{ agent_id='memory_curator'; interval_seconds=60; enabled=$true } | ConvertTo-Json) `
  -ContentType 'application/json').Content | ConvertFrom-Json

# List active agents
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/autonomy/agents/list).Content | ConvertFrom-Json

# Stop agent
(Invoke-WebRequest -UseBasicParsing http://localhost:8000/autonomy/agents/stop/memory_curator -Method POST).Content | ConvertFrom-Json
```

---

## Custom GPT Integration

### Update your GPT's action schema
Point to these endpoints:

**Base URL**: `https://gateway-896380409704.us-east1.run.app`

**Key endpoints**:
- `/mcp/listMCPTools` - List all MCP tools
- `/mcp/executeMCPTool` - Execute tools
- `/mcp/openapi` - OpenAPI spec with x-mcp-attach-ready
- `/credentials/list` - List credential types
- `/credentials/get` - Get credentials (requires auth)
- `/autonomy/agents/start` - Start autonomous agents
- `/autonomy/capabilities` - List all autonomous capabilities

**Authentication**:
Add custom header: `X-MCP-KEY: INVESTORS-DEMO-KEY-2025`
For credentials: `X-Credential-Token: INVESTORS-DEMO-KEY-2025`

---

## Maximum Autonomy Features

### 1. Autonomous Agents
Background agents run continuously:
- **Memory Curator**: Optimizes Firestore memory, dedupes, archives
- **Intelligence Monitor**: Watches intelligence endpoints, alerts on anomalies
- **Credential Rotator**: Checks credential expiry, rotates when needed
- **Auto Builder**: Watches for code changes, auto-builds and deploys

### 2. Cloud Scheduler Triggers
Automated execution on schedule:
- Memory curation every 5 minutes
- Intelligence monitoring every minute
- Auto-builds every 5 minutes
- Credential checks daily at 3 AM
- Protocol rehydration hourly

### 3. Governance & Safety
All autonomous operations:
- Logged to Firestore for audit
- Rate-limited by governance level
- Require approval for CRITICAL operations
- Can be paused/stopped via API
- Have rollback mechanisms

### 4. Self-Healing
System can:
- Auto-restart failed agents
- Rehydrate protocol on boot
- Recover from Firestore failures
- Inject credentials on demand
- Auto-scale Cloud Run instances

---

## Monitoring & Control

### View system status
```bash
curl $GATEWAY_URL/api/status
```

### View active agents
```bash
curl $GATEWAY_URL/autonomy/agents/list
```

### View credential audit log
```bash
curl -H "X-Credential-Token: $TOKEN" $GATEWAY_URL/credentials/audit
```

### View Firestore memory
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager\workspace-sa.json"
$env:FIRESTORE_PROJECT="infinity-x-one-systems"
python .\inspect_firestore.py
```

### Emergency stop all agents
```bash
# Stop specific agent
curl -X POST $GATEWAY_URL/autonomy/agents/stop/memory_curator

# Pause all Cloud Scheduler jobs
gcloud scheduler jobs pause memory-curator-trigger --location=us-east1
gcloud scheduler jobs pause intelligence-monitor-trigger --location=us-east1
gcloud scheduler jobs pause auto-builder-trigger --location=us-east1
gcloud scheduler jobs pause credential-check-trigger --location=us-east1
```

---

## What Makes This Max Autonomy

1. **Zero Manual Intervention**: Agents run on schedule, self-heal, auto-scale
2. **Credential Self-Service**: Can inject credentials without manual key management
3. **Memory Persistence**: Firestore stores all state, survives restarts
4. **Governance First**: All operations governed, audited, rate-limited
5. **Cloud-Native**: Uses Cloud Run, Scheduler, Secret Manager, Firestore
6. **Always-On**: Min 1 instance, health checks, auto-restart
7. **Extensible**: Easy to add new agents, triggers, tools

---

## Next-Level Unlocks

### 1. Add Event-Driven Triggers
Instead of just cron, trigger on:
- Firestore document changes
- Pub/Sub messages
- Cloud Storage uploads
- HTTP webhooks

### 2. Multi-Region Deployment
Deploy to multiple regions for:
- Global low-latency access
- Regional failover
- Data residency compliance

### 3. Agent Learning
Add feedback loops:
- Agents learn from past decisions
- Optimize scheduling based on usage
- Auto-tune parameters

### 4. External Integrations
Connect to:
- Slack for notifications
- PagerDuty for alerts
- GitHub Actions for CI/CD
- Datadog for monitoring

### 5. Advanced Governance
- Multi-level approval workflows
- Policy-as-code (OPA)
- Compliance reporting
- Cost tracking per agent

---

## Production Checklist

- [ ] Service account created with minimal permissions
- [ ] Secrets stored in Secret Manager (not env vars)
- [ ] Cloud Run configured with Workload Identity
- [ ] Cloud Scheduler jobs deployed
- [ ] Firestore indexes created (if needed)
- [ ] Monitoring dashboards set up
- [ ] Alert policies configured
- [ ] Backup/restore tested
- [ ] Rate limits tuned
- [ ] Custom domain configured (optional)
- [ ] CDN configured (optional)
- [ ] Load testing completed

---

## Support & Troubleshooting

### Common Issues

**Agents not starting**: Check Cloud Scheduler logs, verify CREDENTIAL_GATEWAY_TOKEN is set

**Credential access denied**: Verify service account has secretmanager.secretAccessor role

**Firestore permission denied**: Verify service account has datastore.user role

**Rate limits**: Tune governance levels in main_extended.py

**Memory issues**: Increase Cloud Run memory allocation

### Logs
```bash
# Gateway logs
gcloud run services logs read gateway --region=us-east1 --project=infinity-x-one-systems --limit=100

# Cloud Scheduler logs
gcloud scheduler jobs describe memory-curator-trigger --location=us-east1

# Build logs
gcloud builds list --limit=5
gcloud builds log <BUILD_ID>
```

---

**Deployment Status**: ✅ Ready to deploy
**Security Level**: Production-ready with governance
**Autonomy Level**: Maximum (agents + triggers + self-healing)
