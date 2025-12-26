# =====================================================================
#  Vision Cortex Launcher
#  MCP-Controlled Script
#  Contract: contracts/vision_cortex_agent_contracts.json
# =====================================================================

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║       VISION CORTEX — 9-Agent Cognitive Pipeline     ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Build TypeScript
Write-Host "🔨 Building TypeScript..." -ForegroundColor Yellow
npm run build

# Run with specified mode
$mode = $args[0]
if (-not $mode) { $mode = "DRY_RUN" }

Write-Host ""
Write-Host "🧠 Running Vision Cortex in $mode mode..." -ForegroundColor Green
Write-Host ""

node dist/index.js --mode=$mode
