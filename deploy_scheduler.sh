# Cloud Scheduler jobs for autonomous triggers
# Deploy with: gcloud scheduler jobs create http ...

## Memory Curator - runs every 5 minutes
gcloud scheduler jobs create http memory-curator-trigger \
  --schedule="*/5 * * * *" \
  --uri="https://gateway-896380409704.us-east1.run.app/autonomy/triggers/execute/memory_curator" \
  --http-method=POST \
  --headers="X-Credential-Token=${CREDENTIAL_GATEWAY_TOKEN}" \
  --location=us-east1 \
  --description="Trigger memory curation agent"

## Intelligence Monitor - runs every minute
gcloud scheduler jobs create http intelligence-monitor-trigger \
  --schedule="* * * * *" \
  --uri="https://gateway-896380409704.us-east1.run.app/autonomy/triggers/execute/intelligence_monitor" \
  --http-method=POST \
  --headers="X-Credential-Token=${CREDENTIAL_GATEWAY_TOKEN}" \
  --location=us-east1 \
  --description="Trigger intelligence monitoring agent"

## Auto Builder - runs every 5 minutes
gcloud scheduler jobs create http auto-builder-trigger \
  --schedule="*/5 * * * *" \
  --uri="https://gateway-896380409704.us-east1.run.app/autonomy/triggers/execute/auto_builder" \
  --http-method=POST \
  --headers="X-Credential-Token=${CREDENTIAL_GATEWAY_TOKEN}" \
  --location=us-east1 \
  --description="Trigger auto-build agent"

## Credential Check - runs daily at 3 AM
gcloud scheduler jobs create http credential-check-trigger \
  --schedule="0 3 * * *" \
  --uri="https://gateway-896380409704.us-east1.run.app/autonomy/triggers/execute/credential_rotator" \
  --http-method=POST \
  --headers="X-Credential-Token=${CREDENTIAL_GATEWAY_TOKEN}" \
  --location=us-east1 \
  --description="Trigger credential rotation check"

## Rehydrate Protocol - runs on startup and every hour
gcloud scheduler jobs create http rehydrate-protocol-trigger \
  --schedule="0 * * * *" \
  --uri="https://gateway-896380409704.us-east1.run.app/api/protocol/rehydrate" \
  --http-method=POST \
  --headers="X-Credential-Token=${CREDENTIAL_GATEWAY_TOKEN}" \
  --location=us-east1 \
  --description="Trigger protocol rehydration"

# List all scheduler jobs
# gcloud scheduler jobs list --location=us-east1

# Delete a job
# gcloud scheduler jobs delete JOB_NAME --location=us-east1

# Pause a job
# gcloud scheduler jobs pause JOB_NAME --location=us-east1

# Resume a job
# gcloud scheduler jobs resume JOB_NAME --location=us-east1
