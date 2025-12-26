param(
    [int]$RunLoopInterval = 60
)
Set-Location $PSScriptRoot
$RepoRoot = (Get-Item "..\").FullName
 $Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
 if (-not (Test-Path $Python)) { Write-Host "ERROR: Python not found at $Python"; exit 2 }

# If GOOGLE_APPLICATION_CREDENTIALS not set but GCP_SECRET_NAME provided, fetch secret to .secrets
if (-not $env:GOOGLE_APPLICATION_CREDENTIALS -and $env:GCP_SECRET_NAME) {
    Write-Host "GOOGLE_APPLICATION_CREDENTIALS not set; trying to fetch secret $env:GCP_SECRET_NAME from Secret Manager"
    $fetcher = Join-Path $RepoRoot '.venv\Scripts\python.exe'
    $script = Join-Path $RepoRoot 'integrations\gcp_secret.py'
    if (Test-Path $script) {
        try {
            $out = & $fetcher $script $env:GCP_SECRET_NAME --project $env:GCP_PROJECT 2>&1
            $out = $out | Select-Object -Last 1
            if ($out) {
                $credPath = $out.Trim()
                if (Test-Path $credPath) {
                    $env:GOOGLE_APPLICATION_CREDENTIALS = $credPath
                    Write-Host "Wrote credentials to $credPath"
                } else {
                    Write-Host "Secret fetch returned path but file missing: $credPath"
                }
            }
        } catch {
            Write-Host "Secret fetch failed: $($_.Exception.Message)"
        }
    } else {
        Write-Host "Secret helper not found at $script"
    }
}
New-Item -ItemType Directory -Path (Join-Path $RepoRoot 'logs') -Force | Out-Null

Write-Host "Starting uvicorn gateway..."
Start-Process -FilePath $Python -ArgumentList '-m','uvicorn','omni_gateway:app','--host','127.0.0.1','--port','8000' -RedirectStandardOutput (Join-Path $RepoRoot 'logs\uvicorn.out.log') -RedirectStandardError (Join-Path $RepoRoot 'logs\uvicorn.err.log') -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host "Starting pipelines.run_loop (interval ${RunLoopInterval}s)..."
Start-Process -FilePath $Python -ArgumentList '-m','pipelines.run_loop',"${RunLoopInterval}" -RedirectStandardOutput (Join-Path $RepoRoot 'logs\runloop.out.log') -RedirectStandardError (Join-Path $RepoRoot 'logs\runloop.err.log') -WindowStyle Hidden
Start-Sleep -Seconds 1

Write-Host "Starting crawler loop (PowerShell)..."
Start-Process -FilePath 'pwsh' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $RepoRoot 'scripts\run_crawler_loop.ps1') -RedirectStandardOutput (Join-Path $RepoRoot 'logs\crawler.out.log') -RedirectStandardError (Join-Path $RepoRoot 'logs\crawler.err.log') -WindowStyle Hidden

Write-Host 'Services start requested. Use check_services.ps1 to inspect status and logs.'
