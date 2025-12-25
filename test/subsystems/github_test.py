import os

def run():
    token = os.getenv("GITHUB_TOKEN")
    status = "success" if token else "skipped"
    return {
        "name": "github",
        "status": status,
        "checks": [
            {"check": "token_present", "result": bool(token)},
            {"check": "pages_status", "result": "pending"}
        ],
        "note": "Set GITHUB_TOKEN to fully enable GitHub tests" if not token else None
    }
