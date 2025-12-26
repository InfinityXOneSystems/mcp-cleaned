# Firebase / GEMINI Setup (Secure)

This document describes how to configure Firebase / Google API credentials for local development and Cloud Run production.

Important: Do NOT commit service account JSON files or API keys to the repository. Use local env or Secret Manager.

Local dev

- Save your service account JSON (or Firebase JSON) to a secure local path, e.g. `C:\Users\JARVIS\keys\workspace-sa.json`.
- Use the PowerShell helper to set environment variables for your shell session:

```powershell
# In your repo root
.\scripts\load_firebase_env.ps1 -JsonPath 'C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager\workspace-sa.json' -ApiKey 'AIzaSyBLlKqSZFazsIusrqHpIhBh99yNtnR4KU0'
```

- Confirm env vars are set (PowerShell):

```powershell
Get-ChildItem Env:GOOGLE_APPLICATION_CREDENTIALS,Env:GEMINI_KEY
```

Cloud Run / Production

- Store the service account JSON in Google Secret Manager and grant Cloud Run service account access to read the secret.
- In Cloud Run service environment variables, add `GOOGLE_APPLICATION_CREDENTIALS` pointing to `/secrets/service-account.json` (the mounted secret path), or use Workload Identity.
- For `GEMINI_KEY`, store the API key in Secret Manager and map it to the environment variable `GEMINI_KEY` for the Cloud Run revision.

Security notes

- Rotate API keys periodically.
- Use least-privilege service accounts.
- Audit access to secrets using Cloud IAM logs.
