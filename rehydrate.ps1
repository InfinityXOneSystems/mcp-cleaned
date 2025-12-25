# =========================================
# INFINITY XOS — REHYDRATE SCRIPT
# Author: Infinity X One Systems
# Mode: Vision Cortex / Quantum Strategist
# =========================================

Write-Host "`n🧠 INFINITY XOS — REHYDRATION STARTING..." -ForegroundColor Cyan

# -----------------------------
# CORE IDENTITY (STATIC)
# -----------------------------
$OWNER_NAME        = "Neo"
$ORG_NAME          = "Infinity X One Systems"
$TIMEZONE          = "America/New_York"
$PRIMARY_REGION    = "us-east1"

# -----------------------------
# CONTROL PLANE ENDPOINTS
# -----------------------------
$MCP_AGENT_BASE        = "https://mcp-agent-896380409704.us-east1.run.app"
$MEMORY_GATEWAY_BASE  = "https://memory-gateway-896380409704.us-east1.run.app"
$ORCHESTRATOR_BASE    = "https://orchestrator-896380409704.us-east1.run.app"

# -----------------------------
# SECRET MANAGER SERVICE ACCOUNT
# -----------------------------
$GCP_SA_SECRET = "projects/896380409704/secrets/workspace-sa-json"

# -----------------------------
# EXECUTION CONTEXT (OPTIONAL)
# -----------------------------
$TENANT_ID     = $env:TENANT_ID
$WORKSPACE_ID  = $env:WORKSPACE_ID
$PROJECT_ID    = $env:GCP_PROJECT_ID

# -----------------------------
# UTILITY: HEALTH CHECK
# -----------------------------
function Test-Endpoint {
    param ($Name, $Url)

    Write-Host "🔍 Checking $Name ..." -NoNewline
    try {
        $response = Invoke-RestMethod -Uri "$Url/health" -Method GET -TimeoutSec 10
        Write-Host " ✅ ONLINE" -ForegroundColor Green
        return $true
    } catch {
        Write-Host " ❌ OFFLINE" -ForegroundColor Red
        return $false
    }
}

# -----------------------------
# STEP 0 — LOAD SERVICE ACCOUNT FROM SECRET MANAGER
# -----------------------------
Write-Host "`n🔐 STEP 0 — LOADING SERVICE ACCOUNT FROM SECRET MANAGER"
try {
    $loadBody = @{ secret_name = $GCP_SA_SECRET } | ConvertTo-Json
    $res = Invoke-RestMethod -Uri "$MCP_AGENT_BASE/gcp/load_service_account" -Method POST -ContentType "application/json" -Body $loadBody -TimeoutSec 20
    Write-Host "✅ Service account loaded to: $($res.path)" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to load service account via MCP agent: $_" -ForegroundColor Red
    exit 1
}

# -----------------------------
# STEP 1 — VERIFY CONTROL PLANE
# -----------------------------
Write-Host "`n🔐 STEP 1 — VERIFYING CONTROL PLANE"

$MCP_OK  = Test-Endpoint "MCP Agent" $MCP_AGENT_BASE
$MEM_OK  = Test-Endpoint "Memory Gateway" $MEMORY_GATEWAY_BASE
$ORCH_OK = Test-Endpoint "Orchestrator" $ORCHESTRATOR_BASE

if (-not ($MCP_OK -and $MEM_OK -and $ORCH_OK)) {
    Write-Host "`n⛔ REHYDRATION FAILED — CONTROL PLANE NOT HEALTHY" -ForegroundColor Red
    exit 1
}

# -----------------------------
# STEP 2 — LOAD CANONICAL MEMORY
# -----------------------------
Write-Host "`n📚 STEP 2 — LOADING CANONICAL MEMORY"

try {
    $memoryPayload = @{
        owner       = $OWNER_NAME
        organization= $ORG_NAME
        scope       = "core"
        limit       = 20
    } | ConvertTo-Json

    $MEMORY_STATE = Invoke-RestMethod `
        -Uri "$MEMORY_GATEWAY_BASE/recall" `
        -Method POST `
        -ContentType "application/json" `
        -Body $memoryPayload

    Write-Host "✅ Memory loaded successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Memory load failed" -ForegroundColor Red
    exit 1
}

# -----------------------------
# STEP 3 — PARSE OBJECTIVES
# -----------------------------
Write-Host "`n🎯 STEP 3 — PARSING ACTIVE OBJECTIVES"

$OBJECTIVES = $MEMORY_STATE.objectives
$ACTIVE_REPOS = $MEMORY_STATE.active_repos
$LAST_DECISIONS = $MEMORY_STATE.last_decisions

Write-Host "• Active Objectives:"
$OBJECTIVES | ForEach-Object { Write-Host "  - $_" }

# -----------------------------
# STEP 4 — DISCOVER MCP TOOLS
# -----------------------------
Write-Host "`n🧰 STEP 4 — DISCOVERING MCP TOOLS"

try {
    $TOOLS = Invoke-RestMethod `
        -Uri "$MCP_AGENT_BASE/tools" `
        -Method GET

    Write-Host "✅ MCP Tools Discovered: $($TOOLS.Count)" -ForegroundColor Green
} catch {
    Write-Host "❌ MCP Tool discovery failed" -ForegroundColor Red
    exit 1
}

# -----------------------------
# STEP 5 — ESTABLISH EXECUTION CONTRACT
# -----------------------------
Write-Host "`n⚙️ STEP 5 — VALIDATING ORCHESTRATOR CONTRACT"

try {
    $ORCH_INFO = Invoke-RestMethod `
        -Uri "$ORCHESTRATOR_BASE/info" `
        -Method GET

    Write-Host "✅ Orchestrator Ready" -ForegroundColor Green
} catch {
    Write-Host "❌ Orchestrator contract validation failed" -ForegroundColor Red
    exit 1
}

# -----------------------------
# STEP 6 — REHYDRATION SUMMARY
# -----------------------------
Write-Host "`n📊 REHYDRATION SUMMARY" -ForegroundColor Cyan
Write-Host "Owner        : $OWNER_NAME"
Write-Host "Organization : $ORG_NAME"
Write-Host "Timezone     : $TIMEZONE"
Write-Host "Region       : $PRIMARY_REGION"
Write-Host "Objectives   : $($OBJECTIVES.Count)"
Write-Host "MCP Tools    : $($TOOLS.Count)"

# -----------------------------
# STEP 7 — NEXT ACTION SEED
# -----------------------------
Write-Host "`n🚀 NEXT ACTION"
Write-Host "System is REHYDRATED."
Write-Host "Ready to execute:"
Write-Host "→ Highest-leverage 7-day outcome"
Write-Host "→ Intelligence scan"
Write-Host "→ Build + Growth loops"

Write-Host "`n🧠 INFINITY XOS — REHYDRATION COMPLETE" -ForegroundColor Green
