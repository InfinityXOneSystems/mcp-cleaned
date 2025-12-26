# Robust crawler loop: runs the crawler demo every hour using Start-Process so the loop is non-blocking
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
$RepoRoot = (Get-Item "..\").FullName
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) {
    Write-Host "ERROR: Python not found at $Python"; exit 1
}
$ReportDir = Join-Path $RepoRoot 'data\reports'
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null

while ($true) {
    $timestamp = Get-Date -Format o
    Write-Host "[crawler-loop] Starting crawl at $timestamp"
    try {
        # Start crawl using the wrapper that ensures SCRAPER_ALLOWED_HOSTS is set
        $psi = Start-Process -FilePath $Python -ArgumentList 'scripts\run_crawler_with_allowlist.py','https://example.com','--pages','10','--depth','1' -NoNewWindow -Wait -PassThru -WorkingDirectory $RepoRoot -ErrorAction Stop
        if ($psi.ExitCode -ne 0) {
            "$timestamp ERROR: crawler exited with code $($psi.ExitCode)" | Out-File -FilePath (Join-Path $ReportDir 'crawler_loop_error.txt') -Append -Encoding utf8
        }
    } catch {
        $err = "${timestamp} EXCEPTION: $($_.Exception.Message)"
        $err | Out-File -FilePath (Join-Path $ReportDir 'crawler_loop_error.txt') -Append -Encoding utf8
    }
    # Sleep for one hour
    Start-Sleep -Seconds 3600
}
