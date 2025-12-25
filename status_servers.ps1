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
    $procId = $null
    if (Test-Path $pidFile) { $procId = Get-Content $pidFile | Select-Object -First 1 }
    $procAlive = $false
    if ($procId) { $procAlive = (Get-Process -Id $procId -ErrorAction SilentlyContinue) -ne $null }
    $portAlive = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue) -ne $null
    $pidDisp = $procId; if (-not $pidDisp) { $pidDisp = '-' }
    Write-Host ("{0} - PID:{1} Proc:{2} Port:{3}" -f $name, $pidDisp, ($(if($procAlive){'UP'}else{'DOWN'})), ($(if($portAlive){'UP'}else{'DOWN'})))
    if (Test-Path $outLog) { Write-Host "  OUT:"; Get-Content $outLog -Tail $TailLines }
    if (Test-Path $errLog) { Write-Host "  ERR:"; Get-Content $errLog -Tail $TailLines }
}

Show-Status "api_gateway" $PortGateway
Show-Status "dashboard_api" $PortDashboard
Show-Status "intelligence_api" $PortIntel
Show-Status "meta_service" $PortMeta
