Results repo scaffold

Structure:
- distressed_properties/
- business_loans/
- personal_loans/
- asset_predictions/
- schema_registry.json  # versioned schema descriptors for normalized outputs
- ingest_hooks/         # scripts to process new files after sync

This repository stores normalized outputs from crawls and extractions.
Follow schema evolution rules in schema_registry.json before adding new columns.

## Quickstart: Initialize remote repo

1. From the MCP repo root, run the init helper to push the local scaffold to your remote:

	powershell -File ops\init_results_repo.ps1 -remoteUrl https://github.com/your-org/results.git

2. Provide credentials with a credential helper (PAT) or via your Git client.

## Scheduling

To run the local watcher every 10 minutes as a Windows Scheduled Task:

1. Register the task (from an elevated PowerShell prompt):

	powershell -File ops\register_results_sync_task.ps1 -scriptPath "$PWD\\ops\\watch_sync_results.ps1" -intervalMinutes 10

2. Confirm the task exists in Task Scheduler (Task Scheduler Library -> MCP_Results_Sync).

## Ingest Hook

Place automation in `ingest_hooks/process_new_reports.py`. This script runs for each new file pushed into the repo by the watcher. Keep it idempotent and fast.

## Syncing Local Credentials (optional)

If you want to mirror local credential artifacts into your credential repo and Google Secret Manager, use the helpers in `ops/` and `scripts/`.

- Preview and sync files (PowerShell):

	powershell -File ops\sync_credentials.ps1 -localCredDir 'C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager' -gitRepoPath 'C:\path\to\local\foundation' -gcpProject 'infinity-x-one-systems' -gcpSecretPrefix 'mcp/'

	The script will list files and ask for confirmation. It will copy files into the local `foundation` repo and add them to Google Secret Manager under the project specified. It will not push to a remote Git automatically — inspect before pushing.

- Sanitize files with Python helper before upload (optional):

	python -m scripts.sync_credentials --src "C:/Users/JARVIS/AppData/Local/InfinityXOne/CredentialManager" --out tmp_sanitized --allowlist allowlist.txt

	The `allowlist.txt` is a newline-separated list of regex patterns; matches will be redacted.

Security note: Keep secrets out of public repos. Review and use encryption (`-EncryptWithGPG`) and commit policies before pushing secrets to any remote.

## If a git push is blocked by GitHub Push Protection

If you see an error like "Push cannot contain secrets" (GH013), it means GitHub's secret scanning blocked your push because one or more commits contain secrets. Typical remediation steps:

- Identify offending commits and file paths (GitHub error will list them). Example paths: `.secrets/infinity-x-one-systems-sa.json`, `secrets/infinity-x-one-systems-sa.json`.
- Do NOT force-push until you understand impact. Recommended steps:
	1. Backup your repo: `git clone --mirror <repo> backup-repo`
	2. Use `git-filter-repo` to remove the secret files from history (see `ops/remove_git_secrets.ps1`).
	3. Rotate any exposed credentials immediately (create new service accounts, revoke keys).
	4. After rewrite, force-push (`git push --force`) and notify collaborators to re-clone.
	5. Optionally, follow GitHub's unblock flow if the secret is intentionally allowed (see GitHub UI link in the push error).

The repository contains `ops/remove_git_secrets.ps1` to help with history rewriting (requires `git-filter-repo`). Use with caution.

## Cleanup helper (recommended)

To perform the removal of flagged secret files and run verification in one concise step, run the wrapper script locally:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\run_cleanup_and_verify.ps1
```

This avoids long inline `-Command` invocations and prints clean, labeled output.


