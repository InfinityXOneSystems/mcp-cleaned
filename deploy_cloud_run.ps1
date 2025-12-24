param(
    [Parameter(Mandatory=$true)][string]$ProjectId,
    [Parameter(Mandatory=$false)][string]$Region = "us-east1",
    [Parameter(Mandatory=$false)][string]$ImageName = "infinity-xos-mcp",
    [Parameter(Mandatory=$true)][string]$McpApiKey
)

Write-Host "Deploying $ImageName to project $ProjectId in region $Region"

# Ensure gcloud is available
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "gcloud CLI is not installed or not available in PATH. Install and authenticate first."
    exit 1
}

gcloud config set project $ProjectId

Write-Host "Submitting build to Cloud Build..."
gcloud builds submit --tag gcr.io/$ProjectId/$ImageName
if ($LASTEXITCODE -ne 0) { Write-Error "gcloud builds submit failed"; exit $LASTEXITCODE }

Write-Host "Deploying to Cloud Run..."
gcloud run deploy $ImageName \
  --image gcr.io/$ProjectId/$ImageName \
  --platform managed \
  --region $Region \
  --allow-unauthenticated=false \
  --set-env-vars MCP_API_KEY="$McpApiKey"

if ($LASTEXITCODE -ne 0) { Write-Error "gcloud run deploy failed"; exit $LASTEXITCODE }

Write-Host "Deployment complete. Retrieving service URL..."
$url = gcloud run services describe $ImageName --platform managed --region $Region --format 'value(status.url)'
Write-Host "Service URL: $url"

Write-Host "You should now be able to access:"
Write-Host "$url/.well-known/ai-plugin.json"
Write-Host "$url/.well-known/openapi.yaml"
Write-Host "$url/.well-known/mcp.json"
