<#
Verify removal of secret files and compare local HEAD with remote origin/main.

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File ops\verify_cleanup.ps1

#>

Write-Host '=== VERIFY: flagged files ==='
Write-Host ' - .secrets/infinity-x-one-systems-sa.json'
git rev-list --all -- .secrets/infinity-x-one-systems-sa.json | ForEach-Object { Write-Host "    commit: $_" }

Write-Host ' - secrets/infinity-x-one-systems-sa.json'
git rev-list --all -- secrets/infinity-x-one-systems-sa.json | ForEach-Object { Write-Host "    commit: $_" }

Write-Host "`n=== REPOSITORY STATUS ==="
Write-Host 'Local repository:'; Write-Host "  $PWD"
Write-Host 'Local HEAD:'
$localHead = git rev-parse HEAD
Write-Host "  $localHead"

Write-Host 'Remote origin/main:'
$remoteRef = git ls-remote origin refs/heads/main
Write-Host "  $remoteRef"

Write-Host "`n=== RECENT LOCAL COMMITS ==="
$recent = git log --oneline -n 10
$recent | ForEach-Object { Write-Host "  $_" }

Write-Host "`nDone. If any 'commit:' lines are printed under the flagged files then those files still exist in history."

# Write a JSON summary for programmatic consumption
$summary = [PSCustomObject]@{
  flagged = @{
    '.secrets/infinity-x-one-systems-sa.json' = (git rev-list --all -- .secrets/infinity-x-one-systems-sa.json | ForEach-Object { $_ })
    'secrets/infinity-x-one-systems-sa.json' = (git rev-list --all -- secrets/infinity-x-one-systems-sa.json | ForEach-Object { $_ })
  }
  localRepository = (Get-Location).Path
  localHead = $localHead
  remoteRef = $remoteRef
  recent = ($recent -join "`n")
}

$jsonPath = Join-Path $PSScriptRoot 'verify_summary.json'
$summary | ConvertTo-Json -Depth 5 | Out-File -FilePath $jsonPath -Encoding utf8
Write-Host "Wrote summary to: $jsonPath"
