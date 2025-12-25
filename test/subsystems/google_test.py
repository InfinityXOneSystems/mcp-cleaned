import os

def run():
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    return {
        "name": "google",
        "status": "success" if creds else "skipped",
        "checks": [
            {"check": "credentials_present", "result": bool(creds)},
            {"check": "list_projects", "result": "pending"}
        ],
        "note": "GOOGLE_APPLICATION_CREDENTIALS not set" if not creds else None
    }
