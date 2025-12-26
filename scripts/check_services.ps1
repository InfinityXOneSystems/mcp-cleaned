Set-Location $PSScriptRoot
$RepoRoot = (Get-Item "..\").FullName
Write-Host "Checking processes for uvicorn and run_loop..."
$procList = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'uvicorn' -or $_.CommandLine -match 'pipelines.run_loop' -or $_.CommandLine -match 'run_crawler_loop.ps1') } | Select-Object ProcessId,CommandLine
if ($procList) {
    $procList | Format-List
} else {
    Write-Host 'No matching processes found.'
}

Write-Host "\nRecent logs (first 200 lines each):\n"
foreach ($f in @('logs\\uvicorn.out.log','logs\\uvicorn.err.log','logs\\runloop.out.log','logs\\runloop.err.log','logs\\crawler.out.log','logs\\crawler.err.log')){
    $full = Join-Path $RepoRoot $f
    if (Test-Path $full) {
        Write-Host "--- $f ---" -ForegroundColor Cyan
        Get-Content $full -Tail 200 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
    }
}

Write-Host "\nRecent crawl reports:"
if (Test-Path (Join-Path $RepoRoot 'data\\reports')){
    Get-ChildItem (Join-Path $RepoRoot 'data\\reports') -File | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Format-Table Name,LastWriteTime -AutoSize
} else {
    Write-Host 'No reports directory found.'
}
