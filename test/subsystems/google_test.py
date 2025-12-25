import os
from google.oauth2 import service_account

def run():
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not path or not os.path.exists(path):
        return {
            "name": "google",
            "status": "skipped",
            "checks": [{"check": "credentials_present", "result": False}],
            "note": "GOOGLE_APPLICATION_CREDENTIALS not set or file missing"
        }

    checks = []
    status = "success"
    try:
        creds = service_account.Credentials.from_service_account_file(path)
        checks.append({"check": "load_service_account", "result": True})
        checks.append({"check": "project_id", "result": getattr(creds, "project_id", None) is not None})
    except Exception as e:
        status = "fail"
        checks.append({"check": "exception", "result": str(e)})

    return {"name": "google", "status": status, "checks": checks}
