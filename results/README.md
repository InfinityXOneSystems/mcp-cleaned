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
