<#
Run the secret-removal workflow and verification with concise output.

Usage (recommended to run locally, not as a single huge -Command):
  powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\run_cleanup_and_verify.ps1

This script calls the destructive cleanup (removes specified paths from history
and force-pushes) and then runs the verification script. It prints only
short, human-friendly messages and the repository folder path.
#>

param(
  [string[]]$PathsToRemove = @('.secrets/infinity-x-one-systems-sa.json','secrets/infinity-x-one-systems-sa.json'),
  [switch]$AutoPush = $true,
  [switch]$ForceFilter = $false
)

Write-Host "Repository: $PWD"

Write-Host 'Starting cleanup: removing sensitive files from history.'
Write-Host "Files:"
foreach ($p in $PathsToRemove) { Write-Host "  - $p" }

# Normalize PathsToRemove: if passed as a single comma-separated string, split it
if ($PathsToRemove -is [string]) {
  $PathsToRemove = $PathsToRemove -split ',' | ForEach-Object { $_.Trim(' "''') }
} elseif (($PathsToRemove -is [array]) -and ($PathsToRemove.Count -eq 1) -and ($PathsToRemove[0] -like '*,*')) {
  $PathsToRemove = $PathsToRemove[0] -split ',' | ForEach-Object { $_.Trim(' "''') }
}

# Call removal script passing the array directly to the named parameter to avoid positional parsing
$remArgs = @{
  pathsToRemove = $PathsToRemove
}
if ($AutoPush) {
  $remArgs['confirmPush'] = $true
  $remArgs['autoConfirm'] = $true
  $remArgs['autoPush'] = $true
} else {
  $remArgs['confirmPush'] = $true
}

if ($ForceFilter) { $remArgs['ForceFilter'] = $true }

& .\ops\remove_git_secrets.ps1 @remArgs

Write-Host 'Cleanup finished. Running verification...'
& .\ops\verify_cleanup.ps1

Write-Host 'Done.'
