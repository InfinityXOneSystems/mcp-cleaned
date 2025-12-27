param(
    [string]$remoteUrl,
    [int]$intervalSeconds = 300
)

if (-not $remoteUrl) {
    Write-Host "Usage: .\ops\watch_sync_results.ps1 -remoteUrl <git-url> [-intervalSeconds 300]"
    exit 1
}

Write-Host "Starting watch sync for $remoteUrl every $intervalSeconds seconds. Press Ctrl+C to stop."
while ($true) {
    try {
        .\clone_and_sync_results.ps1 -remoteUrl $remoteUrl
    } catch {
        Write-Host "Sync error: $_"
    }
    Start-Sleep -Seconds $intervalSeconds
}
