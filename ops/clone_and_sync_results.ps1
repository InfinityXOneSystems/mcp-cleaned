param(
    [string]$remoteUrl,
    [string]$targetDir = "$PSScriptRoot\..\results_repo"
)

if (-not $remoteUrl) {
    Write-Host "Usage: .\ops\clone_and_sync_results.ps1 -remoteUrl <git-url> [-targetDir <path>]"
    exit 1
}

$targetPath = Resolve-Path -Path $targetDir -ErrorAction SilentlyContinue
if (-not $targetPath) {
    # clone
    Write-Host "Cloning $remoteUrl to $targetDir"
    git clone $remoteUrl $targetDir
} else {
    # pull
    Write-Host "Pulling latest in $targetDir"
    Push-Location $targetDir
    git pull --recurse-submodules
    Pop-Location
}

Write-Host "Sync complete."
