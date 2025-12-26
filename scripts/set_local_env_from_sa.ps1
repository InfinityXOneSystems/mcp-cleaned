<#
PowerShell helper: Load service-account JSON into process env and update local .env file safely (non-committal)
Usage: .\set_local_env_from_sa.ps1 -SaPath C:\path\to\sa.json -ProjectId infinity-x-one-systems
#>
param(
  [Parameter(Mandatory=$true)]
  [string]$SaPath,
  [Parameter(Mandatory=$false)]
  [string]$ProjectId = 'infinity-x-one-systems'
)

if (-not (Test-Path $SaPath)) { Write-Error "Service account JSON not found: $SaPath"; exit 1 }

# Set for this process only
[Environment]::SetEnvironmentVariable('GOOGLE_APPLICATION_CREDENTIALS', $SaPath, 'Process')
[Environment]::SetEnvironmentVariable('FIRESTORE_PROJECT', $ProjectId, 'Process')
Write-Host "Process env set: GOOGLE_APPLICATION_CREDENTIALS=$SaPath; FIRESTORE_PROJECT=$ProjectId"

# Optionally update local .env (create .env.local) but do not commit
$envFile = Join-Path (Get-Location) '.env.local'
"GOOGLE_APPLICATION_CREDENTIALS=$SaPath" | Out-File -FilePath $envFile -Encoding utf8 -Append
"FIRESTORE_PROJECT=$ProjectId" | Out-File -FilePath $envFile -Encoding utf8 -Append
Write-Host ".env.local written (DO NOT commit): $envFile"
