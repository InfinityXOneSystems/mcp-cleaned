# PowerShell helper: load Firebase/GCP credentials into current session (non-persistent)
# Usage: .\load_firebase_env.ps1 -JsonPath C:\path\to\service-account.json -ApiKey 'AIza...'
param(
  [Parameter(Mandatory=$true)]
  [string]$JsonPath,

  [Parameter(Mandatory=$false)]
  [string]$ApiKey
)

if (-not (Test-Path $JsonPath)) {
  Write-Error "Service account JSON not found at $JsonPath"
  exit 1
}

# Set env vars for this process only
[Environment]::SetEnvironmentVariable('GOOGLE_APPLICATION_CREDENTIALS', $JsonPath, 'Process')
if ($ApiKey) { [Environment]::SetEnvironmentVariable('GEMINI_KEY', $ApiKey, 'Process') }
Write-Host "Set GOOGLE_APPLICATION_CREDENTIALS (process) to $JsonPath"
if ($ApiKey) { Write-Host "Set GEMINI_KEY (process)" }

Write-Host "You can now run: python -m uvicorn omni_gateway:app --host 0.0.0.0 --port 8000"