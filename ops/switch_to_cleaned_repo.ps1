param(
    [string]$CleanedUrl = 'https://github.com/InfinityXOneSystems/mcp-cleaned.git',
    [switch]$DryRun
)

Write-Host "Switching local repo remotes to cleaned repo: $CleanedUrl"

if ($DryRun) {
    Write-Host "Dry run: showing commands that would be executed..."
    Write-Host "git remote set-url origin $CleanedUrl"
    Write-Host "git fetch origin"
    Write-Host "git checkout -B main origin/main"
    return
}

git remote set-url origin $CleanedUrl
git fetch origin
git checkout -B main origin/main

Write-Host "Done. Your local 'origin' now points to the cleaned repository."
