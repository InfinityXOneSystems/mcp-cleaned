import os


def run():
    url = os.getenv("ORCHESTRATOR_URL")
    return {
        "name": "orchestrator",
        "status": "success" if url else "skipped",
        "checks": [
            {"check": "endpoint_present", "result": bool(url)},
            {"check": "status_endpoint", "result": "pending"},
        ],
        "note": "ORCHESTRATOR_URL not set" if not url else None,
    }
