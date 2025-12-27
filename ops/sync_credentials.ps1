<#
Sync local credential files to GitHub repo and Google Secret Manager.

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File ops\sync_credentials.ps1 \
    -localCredDir 'C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager' \
    -gitRepoPath 'C:\path\to\local\foundation' \
    -gcpProject 'infinity-x-one-systems' \
    -gcpSecretPrefix 'mcp/'

This script is intentionally conservative: it lists files, prompts for confirmation,
optionally encrypts payloads with gpg (if available), and then writes to local Git
and to GCP Secret Manager. You must have `gcloud` authenticated for the target
project and `git` configured for the target repo.
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$localCredDir = 'C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager',

    [Parameter(Mandatory=$false)]
    [string]$gitRepoPath = 'C:\AI\repos\foundation',

    [Parameter(Mandatory=$false)]
    [string]$gcpProject = 'infinity-x-one-systems',

    [Parameter(Mandatory=$false)]
    [string]$gcpSecretPrefix = 'mcp/',

    [switch]$EncryptWithGPG
)

if (-not (Test-Path $localCredDir)) { Write-Error "Local credential dir not found: $localCredDir"; exit 1 }
Write-Host "Found credential dir: $localCredDir"

$files = Get-ChildItem -Path $localCredDir -File -Recurse
if ($files.Count -eq 0) { Write-Host 'No files found to sync.'; exit 0 }

Write-Host "Files to sync:`n"; $files | ForEach-Object { Write-Host " - $_.FullName" }

$ok = Read-Host 'Proceed to sync these files? Type YES to continue'
if ($ok -ne 'YES') { Write-Host 'Aborted by user.'; exit 0 }

# Ensure local git repo exists
if (-not (Test-Path $gitRepoPath)) {
    Write-Host "Local git repo path not found: $gitRepoPath"; $initRepo = Read-Host 'Create it now? (YES to create)'
    if ($initRepo -ne 'YES') { Write-Host 'Abort.'; exit 1 }
    New-Item -ItemType Directory -Path $gitRepoPath | Out-Null
    Push-Location $gitRepoPath
    git init | Out-Null
    Pop-Location
}

foreach ($f in $files) {
    $rel = $f.FullName.Substring($localCredDir.Length).TrimStart('\')
    $dest = Join-Path $gitRepoPath $rel
    $destDir = Split-Path $dest -Parent
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item -Path $f.FullName -Destination $dest -Force
    Write-Host "Copied $($f.Name) -> $dest"

    # Optionally push to GCP Secret Manager
    $secretName = ($gcpSecretPrefix + $rel) -replace '[^a-zA-Z0-9\/_-]', '_'
    $secretId = $secretName -replace '/','__'

    Write-Host "Preparing secret: $secretId"
    $tmp = [IO.Path]::GetTempFileName()
    Get-Content -Path $f.FullName -Raw | Out-File -FilePath $tmp -Encoding utf8

    if ($EncryptWithGPG) {
        $gpg = Get-Command gpg -ErrorAction SilentlyContinue
        if ($null -eq $gpg) { Write-Warning 'gpg not found; skipping encryption'; }
        else {
            & gpg --yes --batch -o ($tmp + '.gpg') -c $tmp
            Move-Item ($tmp + '.gpg') $tmp -Force
        }
    }

    # Create the secret if needed and add a new version
    $exists = & gcloud secrets list --project $gcpProject --filter "name:$secretId" --format="value(name)" 2>$null
    if (-not $exists) {
        Write-Host "Creating secret $secretId in project $gcpProject"
        & gcloud secrets create $secretId --project $gcpProject --replication-policy="automatic" 2>$null
    }
    Write-Host "Adding secret version for $secretId"
    & gcloud secrets versions add $secretId --project $gcpProject --data-file=$tmp 2>$null
    Remove-Item $tmp -Force
}

# Commit and push to local git repo
Push-Location $gitRepoPath
git add .
$commitMsg = "Sync credentials from local at $(Get-Date -Format o)"
git commit -m $commitMsg 2>$null
Write-Host 'Local credentials copied into repo. Remember to push to remote manually or configure remote and push now.'
Pop-Location

Write-Host 'Done. Review the local repo and remote before sharing.'
