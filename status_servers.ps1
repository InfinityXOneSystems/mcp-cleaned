<#
Show status of Infinity XOS services and recent log tail
#>
param(
    [int]$PortGateway = 8000,
    [int]$PortDashboard = 8001,
    [int]$PortIntel = 8002,
    [int]$PortMeta = 8003,
    [int]$TailLines = 5
)

function Show-Status($name, $port) {
    $pidFile = Join-Path $PWD ("logs/" + $name + ".pid")
    $outLog = Join-Path $PWD ("logs/" + $name + ".out.log")
    $errLog = Join-Path $PWD ("logs/" + $name + ".err.log")
    $pid = (Test-Path $pidFile) ? (Get-Content $pidFile | Select-Object -First 1) : $null
    $procAlive = $false
    if ($pid) { $procAlive = (Get-Process -Id $pid -ErrorAction SilentlyContinue) -ne $null }
    $portAlive = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue) -ne $null
    Write-Host ("{0} — PID:{1} Proc:{2} Port:{3}" -f $name, ($pid ?? '-'), ($procAlive ? 'UP' : 'DOWN'), ($portAlive ? 'UP' : 'DOWN'))
    if (Test-Path $outLog) { Write-Host "  OUT:"; Get-Content $outLog -Tail $TailLines }
    if (Test-Path $errLog) { Write-Host "  ERR:"; Get-Content $errLog -Tail $TailLines }
}

Show-Status "api_gateway" $PortGateway
Show-Status "dashboard_api" $PortDashboard
Show-Status "intelligence_api" $PortIntel
Show-Status "meta_service" $PortMeta
