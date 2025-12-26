# Security Rotation & Revocation

This document outlines steps to rotate or revoke service account keys and API keys safely.

1) Rotate service account key
- In GCP Console -> IAM & Admin -> Service Accounts -> Select service account -> Keys -> Add Key -> Create new key (JSON). Download the new JSON.
- Upload the new JSON to Secret Manager (see scripts/upload_sa_to_secret_manager.sh).
- Deploy a new Cloud Run revision with the secret mounted (see scripts/upload_sa_to_secret_manager.sh message).
- After new revision is running, delete the old key from the service account and remove old secret versions.

2) Revoke API key (GEMINI_KEY)
- In Google Cloud Console -> APIs & Services -> Credentials -> Select API Key -> Delete or restrict.
- Create a new API key, restrict it to required APIs and IPs, and update Secret Manager or Cloud Run env.

3) Update local development
- Replace `.env.local` entries (or use `scripts/set_local_env_from_sa.ps1`) to point at the new JSON path.
- Revoke the old JSON file if stored insecurely.

Note: Never commit secrets to the repository. Use Secret Manager and controlled role-based access.
