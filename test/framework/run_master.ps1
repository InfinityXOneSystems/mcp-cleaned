param(
  [switch]$Full
)

Write-Host "[Master] Starting system tests..."
# Ensure MCP server is running (optional, start quietly with logs)
$serverProc = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*python.exe" }
if (-not $serverProc) {
  Write-Host "[Master] MCP server not detected; starting..."
  $logDir = Join-Path $PWD "logs"
  if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

  $outLog = Join-Path $logDir "mcp_server.out.log"
  $errLog = Join-Path $logDir "mcp_server.err.log"

  $proc = Start-Process -FilePath "python" -ArgumentList @('-u','main_extended.py') -NoNewWindow -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru -WorkingDirectory $PWD
  if ($proc) {
    Set-Content -Path (Join-Path $logDir "mcp_server.pid") -Value $proc.Id
    Write-Host "[Master] MCP server started (PID: $($proc.Id)). Logs: $outLog"
  } else {
    Write-Warning "[Master] Failed to start MCP server; proceeding with tests."
  }
  Start-Sleep -Seconds 3
}

# Run master test as module to ensure package imports
python -m test.master_system_test --mode full

# Trigger maintenance pipeline
Write-Host "[Master] Running maintenance modules..."
python maintain\auto_analyze\analyze.py
python maintain\auto_diagnose\diagnose.py
python maintain\auto_validate\validate.py
python maintain\auto_recommend\recommend.py
python maintain\auto_fix\fix.py
python maintain\auto_heal\heal.py
python maintain\auto_optimize\optimize.py
python maintain\auto_evolve\evolve.py

Write-Host "[Master] Completed system tests + maintenance."
