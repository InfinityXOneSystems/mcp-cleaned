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

deploy gateway 8000
deploy dashboard 8001
deploy intelligence 8002
deploy orchestrator 8080
deploy memory-gateway 8003

echo "Cloud Run deploy complete."
