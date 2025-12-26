P1 SECRETS HYGIENE — MANDATORY PROCEDURE

AUTHORITY
This procedure is mandatory for all demos and production deployments.

CURRENT STATE (DECEMBER 26, 2025)
- credentials-gcp-local.json PRESENT in repo ❌
- secrets_infinityxone_credentials.json PRESENT in repo ❌
- firebase_config.json PRESENT in repo ❌
- These files contain service account keys and must be removed

IMMEDIATE ACTION REQUIRED

1. Remove Credential Files from Repo

```powershell
git rm --cached credentials-gcp-local.json
git rm --cached secrets_infinityxone_credentials.json
git rm --cached firebase_config.json
git commit -m "sec: remove credential files from repo"
git push origin main
```

2. Update .gitignore

Add to .gitignore:
```
# Service account keys
*credentials*.json
secrets_*.json
firebase_config.json
*.pem
*.key
```

3. Move Credentials to Secure Location

Local development:
```powershell
$credDir = "$env:APPDATA\InfinityXOne\CredentialManager"
New-Item -ItemType Directory -Force -Path $credDir
Move-Item credentials-gcp-local.json "$credDir\workspace-sa.json"
```

Set environment variable:
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="$env:APPDATA\InfinityXOne\CredentialManager\workspace-sa.json"
```

4. Cloud Run (Production)

Use Workload Identity Federation:
```yaml
# cloudbuild.yaml or Cloud Run config
serviceAccount: omni-gateway@infinity-x-one-systems.iam.gserviceaccount.com
```

Do NOT mount service account JSON in Cloud Run.

5. Rotate Keys

If credentials were committed to git history:
1. Revoke all service account keys in GCP Console
2. Create new service account keys
3. Update local and Cloud Run configurations
4. Never commit keys again

6. Use Secret Manager

For API keys and tokens:
```bash
# Store secret
gcloud secrets create MCP_API_KEY --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding MCP_API_KEY \
  --member='serviceAccount:omni-gateway@infinity-x-one-systems.iam.gserviceaccount.com' \
  --role='roles/secretmanager.secretAccessor'
```

Access in code:
```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/infinity-x-one-systems/secrets/MCP_API_KEY/versions/latest"
response = client.access_secret_version(request={"name": name})
MCP_API_KEY = response.payload.data.decode("UTF-8")
```

VERIFICATION

Run after cleanup:
```powershell
python p1_verify.py
```

Expected output:
✓ credentials-gcp-local.json not in repo
✓ secrets_infinityxone_credentials.json not in repo
✓ firebase_config.json not in repo

DEMO CHECKLIST

Before any demo:
- [ ] No .json credential files in repo
- [ ] GOOGLE_APPLICATION_CREDENTIALS set to external path
- [ ] MCP_API_KEY rotated and not default
- [ ] Service account keys < 90 days old
- [ ] Workload Identity configured for Cloud Run

NEVER
- Commit service account JSON to git
- Use default keys in demos
- Mount credentials in container images
- Share keys via Slack/email
- Reuse keys across environments
