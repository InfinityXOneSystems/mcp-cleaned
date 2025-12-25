# Start Trading and Intelligence APIs
param(
    [int]$PortDashboard = 8001,
    [int]$PortIntel = 8002
)

Write-Host "Stopping processes on ports $PortDashboard and $PortIntel..."
Get-NetTCPConnection -LocalPort $PortDashboard -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $PortIntel -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Write-Host "Starting dashboard_api.py (port $PortDashboard)..."
Start-Process powershell -ArgumentList "-NoProfile -Command python dashboard_api.py" | Out-Null

Start-Sleep -Seconds 1

Write-Host "Starting intelligence_api.py (port $PortIntel)..."
Start-Process powershell -ArgumentList "-NoProfile -Command python intelligence_api.py" | Out-Null

Start-Sleep -Seconds 1

Write-Host "Opening SPA at http://localhost:$PortDashboard/ ..."
Start-Process "http://localhost:$PortDashboard/"
