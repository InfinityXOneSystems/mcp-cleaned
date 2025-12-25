# Creates a Windows Scheduled Task to run Infinity XOS master tests every ~4 hours
$TaskName = "InfinityXOS-MasterTests"
$WorkingDir = "C:\AI\repos\mcp"
$ScriptPath = Join-Path $WorkingDir "test\framework\run_master.ps1"

Write-Host "Registering scheduled task: $TaskName"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File \"$ScriptPath\""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force

Write-Host "Scheduled task created. It will run every 4 hours."
