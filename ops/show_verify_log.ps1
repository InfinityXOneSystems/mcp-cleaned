<#
Run `verify_cleanup.ps1`, capture output to a log file, and open it in Notepad.
This is useful when the terminal or tooling echoes invocation prefixes (Path[...] lines).

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\show_verify_log.ps1
#>

$log = Join-Path $PSScriptRoot 'verify_output.log'
if (Test-Path $log) { Remove-Item $log -Force }

Write-Host "Running verification and writing to $log"

# Run the verify script and capture output
& "$PSScriptRoot\verify_cleanup.ps1" *>&1 | Out-File -FilePath $log -Encoding utf8

Write-Host "Opening log in Notepad: $log"
Start-Process notepad.exe $log

Write-Host 'Done.'
