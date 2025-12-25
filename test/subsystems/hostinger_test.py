import os

def run():
    api_key = os.getenv("HOSTINGER_API_KEY")
    return {
        "name": "hostinger",
        "status": "success" if api_key else "skipped",
        "checks": [
            {"check": "api_key_present", "result": bool(api_key)},
            {"check": "list_domains", "result": "pending"}
        ],
        "note": "HOSTINGER_API_KEY not set" if not api_key else None
    }
