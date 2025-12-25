<#
Stop all Infinity XOS services using PID files, with fallback by ports
#>
param(
    [int]$PortGateway = 8000,
    [int]$PortDashboard = 8001,
    [int]$PortIntel = 8002,
    [int]$PortMeta = 8003
)

function Stop-ByPid($name) {
    $pidFile = Join-Path $PWD ("logs/" + $name + ".pid")
    if (Test-Path $pidFile) {
        try {
            $pid = Get-Content $pidFile | Select-Object -First 1
            if ($pid) {
                Write-Host ("Stopping {0} (PID {1})" -f $name, $pid)
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Remove-Item $pidFile -ErrorAction SilentlyContinue
            }
        } catch {}
    }
}

Stop-ByPid "api_gateway"
Stop-ByPid "dashboard_api"
Stop-ByPid "intelligence_api"
Stop-ByPid "meta_service"

# Fallback: kill by port
foreach ($p in @($PortGateway, $PortDashboard, $PortIntel, $PortMeta)) {
    Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Write-Host "All services stopped."
