import os
import httpx

def run():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {
            "name": "github",
            "status": "skipped",
            "checks": [{"check": "token_present", "result": False}],
            "note": "Set GITHUB_TOKEN to enable GitHub API checks"
        }

    checks = []
    status = "success"
    try:
        # Basic user check
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        resp = httpx.get("https://api.github.com/user", headers=headers, timeout=10)
        checks.append({"check": "user_auth", "result": resp.status_code == 200})
        if resp.status_code != 200:
            status = "fail"
        # Repo list sample
        resp2 = httpx.get("https://api.github.com/user/repos?per_page=5", headers=headers, timeout=10)
        checks.append({"check": "list_repos", "result": resp2.status_code == 200})
        if resp2.status_code != 200:
            status = "fail"
    except Exception as e:
        status = "fail"
        checks.append({"check": "exception", "result": str(e)})

    return {"name": "github", "status": status, "checks": checks}
