<#
Remove sensitive files from git history using git-filter-repo.

This is a destructive operation on history. Do NOT run without reading and
understanding the consequences. You will likely need to force-push and
coordinate with collaborators.

Prerequisites:
- `git-filter-repo` installed and available on PATH. On Windows use the
  instructions at https://github.com/newren/git-filter-repo
- Backup your repo before running: `git clone --mirror <repo> backup-repo`.

Usage (DRY-RUN):
  powershell -File ops\remove_git_secrets.ps1 -pathsToRemove '.secrets/infinity-x-one-systems-sa.json','secrets/infinity-x-one-systems-sa.json' -dryRun

To actually rewrite history and force-push (must confirm):
  powershell -File ops\remove_git_secrets.ps1 -pathsToRemove 'path1','path2' -confirmPush

#>

param(
  [Parameter(Mandatory=$true)]
  [string[]]$pathsToRemove,

  [switch]$dryRun,
  [switch]$confirmPush,
  [switch]$autoConfirm,
  [switch]$autoPush,
  [switch]$ForceFilter
)

function Test-FilterRepoInstalled {
  $cmd = Get-Command git-filter-repo -ErrorAction SilentlyContinue
  if ($null -ne $cmd) { return $true }
  $py = Get-Command python -ErrorAction SilentlyContinue
  if ($null -ne $py) {
    try {
      & python -c "import importlib,sys; sys.exit(0) if importlib.util.find_spec('git_filter_repo') else sys.exit(2)"
      if ($LASTEXITCODE -eq 0) { return $true }
    } catch { }
  }
  return $false
}

if (-not (Test-FilterRepoInstalled)) {
  Write-Error 'git-filter-repo not found in PATH and python git_filter_repo module not available. Install git-filter-repo or `pip install git-filter-repo` and retry.'; exit 1
}

Write-Host 'Paths to remove from history:'
$pathsToRemove | ForEach-Object { Write-Host " - $_" }

if ($dryRun) {
    Write-Host 'Dry run: Will show what would be removed. No history rewrite performed.'
    $pathsCsv = $pathsToRemove -join ' '
    Write-Host "Run git-filter-repo to simulate (no direct dry-run mode):\n  git filter-repo --path $pathsCsv --invert-paths --analyze"
    exit 0
}

$confirm = 'I_UNDERSTAND'
if (-not $autoConfirm) {
  $confirm = Read-Host 'This will rewrite history. Type I_UNDERSTAND to continue'
}
if ($confirm -ne 'I_UNDERSTAND') { Write-Host 'Aborting.'; exit 0 }
# Build filter arguments
$filterArgs = @('--invert-paths')
foreach ($p in $pathsToRemove) {
  Write-Host "Removing: $p"
  $filterArgs += '--path'
  $filterArgs += $p
}

if ($ForceFilter) { $filterArgs += '--force' }

# Create a fresh mirror clone from the remote origin to operate on
$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) { Write-Error 'No origin remote configured. Set a remote and retry.'; exit 1 }

$ts = Get-Date -Format yyyyMMddHHmmss
$mirror = Join-Path $env:TEMP "mcp-mirror-$ts.git"
if(Test-Path $mirror){ Remove-Item $mirror -Recurse -Force }

Write-Host "Creating mirror from origin ($remoteUrl): $mirror"
& git clone --mirror $remoteUrl $mirror
if($LASTEXITCODE -ne 0){ Write-Error 'git clone --mirror failed'; exit 1 }

Write-Host 'MIRROR_CREATED:'
Write-Host $mirror

Write-Host 'Running git-filter-repo in mirror...'

# Prefer git-filter-repo if available, otherwise use python -m git_filter_repo
$cmd = Get-Command git-filter-repo -ErrorAction SilentlyContinue
if ($null -ne $cmd) {
  & git -C $mirror filter-repo $filterArgs
  if($LASTEXITCODE -ne 0){ Write-Error 'git-filter-repo failed'; Remove-Item $mirror -Recurse -Force; exit 1 }
} else {
  Write-Host 'git-filter-repo not on PATH; attempting python -m git_filter_repo fallback.'
  Push-Location $mirror
  & python -m git_filter_repo $filterArgs
  $rc = $LASTEXITCODE
  Pop-Location
  if($rc -ne 0){ Write-Error 'python -m git_filter_repo failed'; Remove-Item $mirror -Recurse -Force; exit 1 }
}

Write-Host 'Filter complete in mirror.'

Write-Host 'Running reflog expire and garbage collection in mirror...'
& git -C $mirror reflog expire --expire=now --all
& git -C $mirror gc --prune=now --aggressive

Write-Host 'Mirror cleaned.'

if ($confirmPush) {
  if(-not $autoPush) {
    $pushConfirm = Read-Host 'Force-push cleaned mirror to origin? Type PUSH to continue'
    if ($pushConfirm -ne 'PUSH') { Write-Host 'Push skipped.'; Remove-Item $mirror -Recurse -Force; exit 0 }
  }
  Write-Host 'Pushing cleaned refs to origin...'
  # Ensure origin is set inside the mirror before pushing
  Push-Location $mirror
  & git remote remove origin 2>$null | Out-Null
  & git remote add origin $remoteUrl
  Pop-Location

  & git -C $mirror push --mirror origin
  if($LASTEXITCODE -ne 0){ Write-Error 'git push --mirror failed'; Remove-Item $mirror -Recurse -Force; exit 1 }
  Write-Host 'Push complete. Cleaning up mirror.'
  Remove-Item $mirror -Recurse -Force
}

  # If ForceFilter is requested, perform an in-place forced rewrite of the working repository
  if ($ForceFilter) {
    Write-Host 'ForceFilter requested: performing in-place forced git-filter-repo on working repo (destructive).'
    Write-Host 'Creating local repo backup as a safety mirror.'
    $backup = Join-Path $env:TEMP "mcp-local-backup-$ts.git"
    if(Test-Path $backup){ Remove-Item $backup -Recurse -Force }
    & git clone --mirror . $backup
    if($LASTEXITCODE -ne 0){ Write-Error 'Failed to create local backup mirror'; exit 1 }

    Write-Host 'Running git-filter-repo in-place (working repo)...'
    $inplaceArgs = $filterArgs
    Push-Location (Get-Location)
    $cmd = Get-Command git-filter-repo -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
      & git filter-repo $inplaceArgs
      if($LASTEXITCODE -ne 0){ Write-Error 'git-filter-repo (in-place) failed'; exit 1 }
    } else {
      Write-Host 'git-filter-repo not on PATH; attempting python -m git_filter_repo fallback (in-place).'
      & python -m git_filter_repo $inplaceArgs
      if($LASTEXITCODE -ne 0){ Write-Error 'python -m git_filter_repo (in-place) failed'; exit 1 }
    }
    Pop-Location

    Write-Host 'Running reflog expire and gc on working repo...'
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive

    Write-Host 'Force-pushing rewritten main to origin...'
    & git push --force origin main:main
    if($LASTEXITCODE -ne 0){ Write-Error 'git push --force failed'; exit 1 }
    Write-Host 'In-place rewrite pushed.'
  }
 
