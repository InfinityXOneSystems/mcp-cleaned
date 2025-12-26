param(
    [string]$serviceName = "mcp-intel",
    [string]$project = $env:GCLOUD_PROJECT,
    [string]$region = "us-central1"
)
docker build -t gcr.io/$project/$serviceName:latest .
docker push gcr.io/$project/$serviceName:latest
gcloud run deploy $serviceName --image gcr.io/$project/$serviceName:latest --region $region --platform managed --allow-unauthenticated
