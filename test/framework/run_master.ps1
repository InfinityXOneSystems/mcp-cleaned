param(
  [switch]$Full
)

Write-Host "[Master] Starting system tests..."
# Ensure MCP server is running
$proc = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq '' }
if (-not $proc) {
  Write-Host "[Master] MCP server not detected; starting..."
  Start-Process python -ArgumentList "main_extended.py" -WindowStyle Hidden
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
