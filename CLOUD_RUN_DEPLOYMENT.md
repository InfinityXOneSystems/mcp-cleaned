# Cloud Run Deployment Configuration

## Single-Service Deployment (Recommended)

Deploy the entire Omni-Gateway as a single Cloud Run service with all capabilities.

### Prerequisites
```bash
# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Set project
export PROJECT_ID=896380409704
gcloud config set project $PROJECT_ID
```

### Build and Deploy

```bash
# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/omni-gateway

# Deploy to Cloud Run
gcloud run deploy omni-gateway \
  --image gcr.io/$PROJECT_ID/omni-gateway \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="GATEWAY_PORT=8080" \
  --set-secrets="GOOGLE_APPLICATION_CREDENTIALS=infinity-x-one-systems-key:latest,MCP_API_KEY=mcp-api-key:latest,GITHUB_TOKEN=github-token:latest"
```

### Environment Variables
```
GATEWAY_PORT=8080
GOOGLE_APPLICATION_CREDENTIALS=/secrets/google-creds.json
MCP_API_KEY=<from-secret-manager>
GITHUB_TOKEN=<from-secret-manager>
SHEET_ID=<your-sheet-id>
CALENDAR_ID=primary
```

### Dockerfile
Already exists in your repo. Current Dockerfile supports:
- Multi-stage build for optimization
- All Python dependencies from requirements.txt
- FastAPI with Uvicorn
- Automatic port detection (Cloud Run sets PORT env var)

### Service Architecture
```
Cloud Run: omni-gateway (single service)
├── API Gateway (api_gateway.py) - Port 8080
├── Dashboard API (dashboard_api.py) - Imported
├── Intelligence API (intelligence_api.py) - Imported
├── Meta Service (meta_service.py) - Imported
└── MCP Server (main_extended.py) - Imported

All services merged into single process for Cloud Run efficiency.
```

### Cost Optimization
- Min instances: 0 (scales to zero when idle)
- Max instances: 10 (autoscales based on load)
- Memory: 2Gi (adjust based on actual usage)
- CPU: 2 (adjust based on load testing)

### Post-Deployment
```bash
# Get service URL
gcloud run services describe omni-gateway --region us-central1 --format='value(status.url)'

# Test endpoints
curl https://omni-gateway-<hash>.run.app/health
curl https://omni-gateway-<hash>.run.app/admin/status
```

## Multi-Service Deployment (Alternative)

For complete isolation, deploy as separate Cloud Run services:

```bash
# Gateway
gcloud run deploy gateway --image gcr.io/$PROJECT_ID/gateway --region us-central1

# Dashboard
gcloud run deploy dashboard --image gcr.io/$PROJECT_ID/dashboard --region us-central1

# Intelligence
gcloud run deploy intelligence --image gcr.io/$PROJECT_ID/intelligence --region us-central1

# Meta
gcloud run deploy meta --image gcr.io/$PROJECT_ID/meta --region us-central1
```

Configure gateway with internal service URLs via environment variables.

## Secrets Management

```bash
# Create secrets
echo -n "your-api-key" | gcloud secrets create mcp-api-key --data-file=-
echo -n "your-github-token" | gcloud secrets create github-token --data-file=-
gcloud secrets create infinity-x-one-systems-key --data-file=path/to/service-account.json

# Grant access
gcloud secrets add-iam-policy-binding mcp-api-key \
  --member="serviceAccount:896380409704-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Domain Mapping

```bash
# Map custom domain
gcloud run domain-mappings create --service omni-gateway --domain api.infinityx.one --region us-central1
```

## Monitoring

- Cloud Run automatically provides logs, metrics, and traces
- Access via: https://console.cloud.google.com/run
- Enable Cloud Monitoring for detailed metrics
- Set up alerts for error rates, latency, and instance count
