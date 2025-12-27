param(
    [string]$taskName = 'MCP_Results_Sync',
    [string]$scriptPath = '$PSScriptRoot\\watch_sync_results.ps1',
    [int]$intervalMinutes = 10
)

if(-not (Test-Path $scriptPath)){
    Write-Host "Script not found: $scriptPath"; exit 1
}

$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $intervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Force

Write-Host "Registered scheduled task '$taskName' to run $scriptPath every $intervalMinutes minutes."
