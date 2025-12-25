<#
Disconnect Infinity-XOS from the local MCP system safely.
This script is non-destructive: it will set doc-evolution to safe, clear any path override,
and run verification checks. It will NOT delete any files or remove submodules.

Run in PowerShell: .\scripts\disconnect_infinity_xos.ps1
#>

Write-Host "Starting safe disconnect of infinity-xos..." -ForegroundColor Cyan

# 1) Set runtime env for this process
$env:DOC_EV_MODE = 'safe'
if (Test-Path Env:DOC_EV_PATH_OVERRIDE) { Remove-Item Env:DOC_EV_PATH_OVERRIDE }

Write-Host "Set DOC_EV_MODE=safe and cleared DOC_EV_PATH_OVERRIDE for current session." -ForegroundColor Green

# 2) Persist suggestion: edit .env or .env.local manually. We will also print the file to help.
$envFile = Join-Path $PSScriptRoot "..\..\.env.example"
if (Test-Path $envFile) {
  Write-Host "Found .env.example at: $envFile" -ForegroundColor Yellow
  Write-Host "Please edit your real .env (do NOT commit) and set DOC_EV_MODE=safe and clear DOC_EV_PATH_OVERRIDE." -ForegroundColor Yellow
} else {
  Write-Host "No .env.example found in repo root." -ForegroundColor Yellow
}

# 3) Run a Python check to call integration setters/getters
Write-Host "Running verification Python check..." -ForegroundColor Cyan
$tmp = [System.IO.Path]::GetTempFileName() + '.py'
$py = @'
import sys, os
sys.path.insert(0, r'c:\AI\repos\mcp')
try:
  from integrations import doc_evolution_integration as dei
  print('get_mode():', dei.get_mode())
  print('get_doc_ev_file():', dei.get_doc_ev_file())
  # Ensure runtime mode is safe
  print('set_mode(safe):', dei.set_mode('safe'))
  print('get_mode(after):', dei.get_mode())
except Exception as e:
  print('Python check failed:', e)
'@
$py | Out-File -FilePath $tmp -Encoding utf8
python $tmp
Remove-Item $tmp -Force

# 4) Report possible junction or workspace references (non-destructive)
Write-Host "Searching for potential junction/mount under mcp pointing to infinity-xos..." -ForegroundColor Cyan
$candidate = Join-Path (Get-Location) 'infinity-xos'
if (Test-Path $candidate) {
    $attr = Get-Item $candidate -Force
    Write-Host "Found path: $candidate" -ForegroundColor Yellow
    Write-Host "Attributes: $($attr.Attributes)" -ForegroundColor Yellow
    Write-Host "(This is only a report; no deletion performed.)" -ForegroundColor Yellow
} else {
    Write-Host "No local junction or folder named 'infinity-xos' found under the current repo." -ForegroundColor Green
}

Write-Host "Disconnect actions completed. Review output above and edit your .env / workspace to finalize." -ForegroundColor Green
