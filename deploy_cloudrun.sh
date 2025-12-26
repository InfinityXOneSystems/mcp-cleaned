#!/usr/bin/env bash
set -euo pipefail
PROJECT="${PROJECT:-your-gcp-project}"
REGION="${REGION:-us-central1}"
IMAGE_PREFIX="${REGION}-docker.pkg.dev/${PROJECT}/mcp"

deploy() {
  local svc=$1
  local port=$2
  gcloud run deploy "$svc" \
    --project "$PROJECT" \
    --region "$REGION" \
    --image "$IMAGE_PREFIX/$svc:latest" \
    --platform managed \
    --allow-unauthenticated \
    --port "$port" \
    --set-env-vars=DOC_EV_MODE=safe
}

# Single-service deploy: only the gateway, which mounts subapps
gcloud run deploy "gateway" \
  --project "$PROJECT" \
  --region "$REGION" \
  --image "$IMAGE_PREFIX/gateway:latest" \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars=DOC_EV_MODE=safe,SERVICE_MODE=single

echo "Cloud Run single-service deploy complete."
