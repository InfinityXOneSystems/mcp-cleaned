#!/usr/bin/env bash
# Upload a local service account JSON to Google Secret Manager and grant access to a Cloud Run service account.
# Usage: ./upload_sa_to_secret_manager.sh /path/to/sa.json your-gcp-project secret-name cloud-run-service-account

set -euo pipefail
if [ "$#" -lt 4 ]; then
  echo "Usage: $0 /path/to/sa.json PROJECT_ID SECRET_NAME CLOUD_RUN_SA_EMAIL"
  exit 1
fi
SA_PATH=$1
PROJECT_ID=$2
SECRET_NAME=$3
CLOUD_RUN_SA=$4

# Create secret
gcloud secrets create $SECRET_NAME --project=$PROJECT_ID --replication-policy="automatic" || true

# Add secret version
gcloud secrets versions add $SECRET_NAME --project=$PROJECT_ID --data-file="$SA_PATH"

# Grant Cloud Run service account access to access the secret
gcloud secrets add-iam-policy-binding $SECRET_NAME \
  --project=$PROJECT_ID \
  --member="serviceAccount:${CLOUD_RUN_SA}" \
  --role="roles/secretmanager.secretAccessor"

echo "Secret uploaded and IAM binding granted. To mount in Cloud Run, add: --set-secrets GOOGLE_APPLICATION_CREDENTIALS=projects/${PROJECT_ID}/secrets/${SECRET_NAME}:latest"

# Example command to deploy Cloud Run with secret (adjust region/service name):
# gcloud run deploy SERVICE_NAME --image IMAGE_URL --region us-east1 --project $PROJECT_ID --add-cloudsql-instances YOUR_INSTANCE --set-secrets GOOGLE_APPLICATION_CREDENTIALS=projects/${PROJECT_ID}/secrets/${SECRET_NAME}:latest
