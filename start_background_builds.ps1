# Start background build loop in a new PowerShell window
Write-Host "Starting background build runner..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$PSScriptRoot'; python background_build_runner.py"