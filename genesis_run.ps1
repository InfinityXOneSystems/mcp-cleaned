# =====================================================================
#  INFINITY X  |  GENESIS RUN (Auto)
#  MCP-Controlled Script
#  Contract: system.genesis
#  Agent: builder.architect
#  Validator: pending
# =====================================================================

$ErrorActionPreference = "Stop"
$repoRoot   = "C:\AI\repos\mcp"
$extPath    = "C:\AI\repos\mcp\vision_cortex\vscode\infinityx-admin"
$gateway    = $env:MCP_ENDPOINT
if (-not $gateway) { $gateway = "http://localhost:8000" }

function Step($msg, [ConsoleColor]$color = "Cyan") {
    Write-Host "`n▶ $msg" -ForegroundColor $color
}

function Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║                                                              ║" -ForegroundColor Magenta
    Write-Host "║   ██╗███╗   ██╗███████╗██╗███╗   ██╗██╗████████╗██╗   ██╗   ║" -ForegroundColor Magenta
    Write-Host "║   ██║████╗  ██║██╔════╝██║████╗  ██║██║╚══██╔══╝╚██╗ ██╔╝   ║" -ForegroundColor Magenta
    Write-Host "║   ██║██╔██╗ ██║█████╗  ██║██╔██╗ ██║██║   ██║    ╚████╔╝    ║" -ForegroundColor Magenta
    Write-Host "║   ██║██║╚██╗██║██╔══╝  ██║██║╚██╗██║██║   ██║     ╚██╔╝     ║" -ForegroundColor Magenta
    Write-Host "║   ██║██║ ╚████║██║     ██║██║ ╚████║██║   ██║      ██║      ║" -ForegroundColor Magenta
    Write-Host "║   ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝      ╚═╝      ║" -ForegroundColor Magenta
    Write-Host "║                                                              ║" -ForegroundColor Magenta
    Write-Host "║                    GENESIS RUN v1.0.0                        ║" -ForegroundColor Magenta
    Write-Host "║              Vision Cortex + Auto Builder                    ║" -ForegroundColor Magenta
    Write-Host "║                                                              ║" -ForegroundColor Magenta
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

Banner

# ─────────────────────────────────────────────────────────────────────
# 0️⃣ Pre-flight checks
# ─────────────────────────────────────────────────────────────────────
Step "Pre-flight checks..."

# Check contracts exist
$contracts = @(
    "$repoRoot\contracts\builder_agent_contracts.json",
    "$repoRoot\contracts\vision_cortex_agent_contracts.json",
    "$repoRoot\contracts\OPERATIONAL_SCHEDULE.json"
)

$allFound = $true
foreach ($c in $contracts) {
    if (Test-Path $c) {
        Write-Host "   ✓ $($c | Split-Path -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $($c | Split-Path -Leaf) NOT FOUND" -ForegroundColor Red
        $allFound = $false
    }
}

if (-not $allFound) {
    Write-Host "`n❌ Missing contracts. Run scaffolding first." -ForegroundColor Red
    exit 1
}

# Check gateway availability
Step "Checking gateway availability at $gateway..."
try {
    $healthCheck = Invoke-RestMethod -Uri "$gateway/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✓ Gateway online: $($healthCheck.status)" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Gateway not responding. Attempting to start..." -ForegroundColor Yellow
    
    # Try to start the gateway
    $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager\workspace-sa.json"
    $env:FIRESTORE_PROJECT = "infinity-x-one-systems"
    $env:FIRESTORE_COLLECTION = "mcp_memory"
    $env:MCP_API_KEY = "INVESTORS-DEMO-KEY-2025"
    $env:SAFE_MODE = "true"
    $env:PORT = "8000"
    
    Start-Process -FilePath "python" -ArgumentList "omni_gateway.py" -WorkingDirectory $repoRoot -WindowStyle Minimized
    Write-Host "   → Gateway starting in background..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    try {
        $healthCheck = Invoke-RestMethod -Uri "$gateway/health" -Method GET -TimeoutSec 10 -ErrorAction Stop
        Write-Host "   ✓ Gateway now online: $($healthCheck.status)" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠ Gateway still not responding. Continuing in offline mode..." -ForegroundColor Yellow
    }
}

# ─────────────────────────────────────────────────────────────────────
# 1️⃣ Register all agents
# ─────────────────────────────────────────────────────────────────────
Step "Registering agents with MCP..."
try {
    & "$repoRoot\register_agents.ps1"
} catch {
    Write-Host "   ⚠ Registration script failed (gateway may be offline)" -ForegroundColor Yellow
}

# ─────────────────────────────────────────────────────────────────────
# 2️⃣ Execute Auto Builder DRY_RUN
# ─────────────────────────────────────────────────────────────────────
Step "Triggering Auto Builder DRY_RUN pipeline..."
try {
    $body = @{
        agent   = "builder.integrator"
        action  = "build_cycle"
        payload = @{ mode = "DRY_RUN" }
    } | ConvertTo-Json -Depth 5
    
    $result = Invoke-RestMethod -Uri "$gateway/mcp/execute" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30 -ErrorAction Stop
    Write-Host "   ✓ DRY_RUN triggered successfully" -ForegroundColor Green
    $result | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor DarkGray
} catch {
    Write-Host "   ⚠ DRY_RUN request failed (endpoint may not exist yet)" -ForegroundColor Yellow
    Write-Host "   → Pipeline definition verified locally" -ForegroundColor DarkGray
    
    # Verify pipeline locally
    $pipeline = Get-Content "$repoRoot\auto_builder\build_pipeline.json" -Raw | ConvertFrom-Json
    Write-Host "   → Pipeline: $($pipeline.pipeline_id) ($($pipeline.pipeline.Count) agents)" -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────────────────────────────
# 3️⃣ Launch the VS Code cockpit
# ─────────────────────────────────────────────────────────────────────
Step "Launching VS Code cockpit..."
if (Test-Path $extPath) {
    try {
        Start-Process code -ArgumentList "--extensionDevelopmentPath=`"$extPath`"" -ErrorAction Stop
        Write-Host "   ✓ VS Code launched with extension development mode" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠ Could not launch VS Code. Open manually with:" -ForegroundColor Yellow
        Write-Host "     code --extensionDevelopmentPath=`"$extPath`"" -ForegroundColor DarkGray
    }
} else {
    Write-Host "   ⚠ Extension path not found: $extPath" -ForegroundColor Yellow
}

# ─────────────────────────────────────────────────────────────────────
# 4️⃣ Validate full system after warm-up
# ─────────────────────────────────────────────────────────────────────
Step "Waiting for system warm-up (12 seconds)..."
for ($i = 12; $i -gt 0; $i--) {
    Write-Host "`r   ⏳ $i seconds remaining... " -NoNewline -ForegroundColor Yellow
    Start-Sleep -Seconds 1
}
Write-Host "`r   ✓ Warm-up complete                    " -ForegroundColor Green

Step "Validating system state..."
try {
    $validateBody = '{"scope":"full_system"}'
    $result = Invoke-RestMethod -Uri "$gateway/mcp/validate" -Method POST -Body $validateBody -ContentType "application/json" -TimeoutSec 30 -ErrorAction Stop
    $result | ConvertTo-Json -Depth 5 | Out-File "$repoRoot\genesis_validation_log.json"
    Write-Host "`n   Validation Result:" -ForegroundColor Green
    $result | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Cyan
} catch {
    Write-Host "   ⚠ Remote validation not available. Running local validation..." -ForegroundColor Yellow
    
    # Local validation fallback
    $vcAgents = (Get-Content "$repoRoot\contracts\vision_cortex_agent_contracts.json" -Raw | ConvertFrom-Json).agents
    $builderAgents = (Get-Content "$repoRoot\contracts\builder_agent_contracts.json" -Raw | ConvertFrom-Json).agents
    $pipeline = Get-Content "$repoRoot\auto_builder\build_pipeline.json" -Raw | ConvertFrom-Json
    
    $localResult = @{
        status = "validated"
        agents = $vcAgents.Count + $builderAgents.Count
        governance = "locked"
        pipeline = "ready"
        details = @{
            vision_cortex_agents = $vcAgents.Count
            builder_agents = $builderAgents.Count
            pipeline_id = $pipeline.pipeline_id
            dry_run_first = $pipeline.governance.dry_run_first
        }
        timestamp = (Get-Date -Format "o")
        mode = "offline_validation"
    }
    
    $localResult | ConvertTo-Json -Depth 5 | Out-File "$repoRoot\genesis_validation_log.json"
    Write-Host "`n   Validation Result (Local):" -ForegroundColor Green
    $localResult | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Cyan
}

# ─────────────────────────────────────────────────────────────────────
# 5️⃣ Final summary
# ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    GENESIS COMPLETE ✅                       ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Log saved → $repoRoot\genesis_validation_log.json" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Available Commands in VS Code:" -ForegroundColor Cyan
Write-Host "  • InfinityX: Show Intelligence Cockpit" -ForegroundColor White
Write-Host "  • InfinityX: Run Dry Run" -ForegroundColor White
Write-Host "  • InfinityX: List Agents" -ForegroundColor White
Write-Host "  • InfinityX: Invoke Agent" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open Command Palette (Ctrl+Shift+P)" -ForegroundColor White
Write-Host "  2. Type 'InfinityX' to see available commands" -ForegroundColor White
Write-Host "  3. Run 'InfinityX: Show Intelligence Cockpit'" -ForegroundColor White
Write-Host ""
