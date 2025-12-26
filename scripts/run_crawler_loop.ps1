# Simple crawler loop: runs the crawler demo every hour and writes errors to data/reports
$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Definition)
while ($true) {
    try {
        Write-Host "[crawler-loop] Running crawl at" (Get-Date -Format o)
        .\.venv\Scripts\python.exe scripts\run_crawler_demo.py https://example.com --pages 10 --depth 1
    } catch {
        $err = "$(Get-Date -Format o) ERROR: $($_.Exception.Message)"
        $err | Out-File -FilePath data\reports\crawler_loop_error.txt -Append -Encoding utf8
    }
    Start-Sleep -Seconds 3600
}
