<#
Start all Infinity XOS services in the background with logs and PID files
Services:
  - Orchestrator Gateway (api_gateway.py) : 8000
  - Trading Dashboard (dashboard_api.py) : 8001
  - Intelligence API (intelligence_api.py): 8002
  - Meta Service (meta_service.py)        : 8003
#>

param(
    [int]$PortGateway = 8000,
    [int]$PortDashboard = 8001,
    [int]$PortIntel = 8002,
    [int]$PortMeta = 8003
)

function Ensure-Dir($path) {
    if (!(Test-Path -Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

Ensure-Dir "logs"

Write-Host "Stopping any running services on ports $PortGateway, $PortDashboard, $PortIntel, $PortMeta ..."
foreach ($p in @($PortGateway, $PortDashboard, $PortIntel, $PortMeta)) {
    Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Start-Sleep -Milliseconds 300

function Start-ServiceBg($name, $script, $port) {
    $outLog = Join-Path $PWD ("logs/" + $name + ".out.log")
    $errLog = Join-Path $PWD ("logs/" + $name + ".err.log")
    $pidFile = Join-Path $PWD ("logs/" + $name + ".pid")
    Write-Host ("Starting {0} on port {1} ..." -f $name, $port)
    $proc = Start-Process -FilePath "python" -ArgumentList $script -NoNewWindow -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    $proc.Id | Out-File -FilePath $pidFile -Encoding ascii
}

# Start orchestrator gateway
$env:GATEWAY_PORT = $PortGateway
Start-ServiceBg -name "api_gateway" -script "api_gateway.py" -port $PortGateway

# Start dashboard API
Start-ServiceBg -name "dashboard_api" -script "dashboard_api.py" -port $PortDashboard

# Start intelligence API
Start-ServiceBg -name "intelligence_api" -script "intelligence_api.py" -port $PortIntel

# Start meta service
Start-ServiceBg -name "meta_service" -script "meta_service.py" -port $PortMeta

Start-Sleep -Seconds 2

Write-Host "Checking health endpoints..."
function Try-Health($url) {
    try { Invoke-RestMethod -Uri $url -TimeoutSec 5 -ErrorAction Stop | Out-Host } catch { Write-Host ("{0} - not responding yet" -f $url) }
}
Try-Health "http://localhost:$PortGateway/health"
Try-Health "http://localhost:$PortDashboard/api/portfolio"
Try-Health "http://localhost:$PortIntel/health"

Write-Host "Services started. Logs in ./logs."
Write-Host "Open gateway: http://localhost:$PortGateway/"
Write-Host "Open dashboard: http://localhost:$PortDashboard/"
Write-Host "Open intelligence: http://localhost:$PortIntel/"
