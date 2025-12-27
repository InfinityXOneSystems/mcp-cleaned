Subject: Repository migrated to cleaned history — action required

Hi team,

We discovered that sensitive credentials were accidentally committed to this repository's history. The credentials were rotated and revoked. Because GitHub's secret scanning blocked force-pushes to the original repository, we created a cleaned canonical copy at:

https://github.com/InfinityXOneSystems/mcp-cleaned

Please do one of the following as soon as convenient:

1) Re-clone from the cleaned repo:

   git clone https://github.com/InfinityXOneSystems/mcp-cleaned.git

2) Or switch your existing clone to the cleaned repo (from your local repository root):

   powershell -NoProfile -ExecutionPolicy Bypass -File ops\switch_to_cleaned_repo.ps1

Notes:
- All exposed keys were rotated. Confirm your local credentials and environment variables do not reference revoked keys.
- CI and deployment configs must be updated to point at the cleaned repository URL.

If you have questions, contact the repo admin.

Thank you for taking prompt action.
