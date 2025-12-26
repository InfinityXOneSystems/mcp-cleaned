# Start Omni Gateway with full MCP integration
# Intelligence Cockpit + 59 MCP Tools + CLI + Autonomous Prompts

Write-Host "🚀 Starting Infinity XOS Omni Gateway..." -ForegroundColor Cyan

# Set environment
$env:SERVICE_MODE = "single"
$env:PORT = "8000"

# Kill existing Python processes
Write-Host "Clearing port 8000..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start gateway
Write-Host "Starting Omni Gateway on port 8000..." -ForegroundColor Green
cd $PSScriptRoot

# Start in new window to keep it running
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; uvicorn omni_gateway:app --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 5

# Test connection
try {
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/status" -ErrorAction Stop
    Write-Host "`n✓ Omni Gateway is LIVE!" -ForegroundColor Green
    Write-Host "✓ Omni Hub: $($status.components.omni_hub)" -ForegroundColor Green
    Write-Host "✓ MCP Tools: $($status.components.mcp_tools)" -ForegroundColor Green
    Write-Host "✓ Cockpit: $($status.components.cockpit)" -ForegroundColor Green
    Write-Host "✓ CLI Integration: $($status.components.cli_integration)" -ForegroundColor Green
    Write-Host "`n🎯 Access Intelligence Cockpit: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📊 API Status: http://localhost:8000/api/status" -ForegroundColor Cyan
    Write-Host "🛠️ API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
} catch {
    Write-Host "`n✗ Gateway not responding yet..." -ForegroundColor Red
    Write-Host "Check the new PowerShell window for startup logs" -ForegroundColor Yellow
}
