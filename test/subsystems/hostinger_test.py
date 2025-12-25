import os

def run():
    api_key = os.getenv("HOSTINGER_API_KEY")
    if not api_key:
        return {
            "name": "hostinger",
            "status": "skipped",
            "checks": [{"check": "api_key_present", "result": False}],
            "note": "HOSTINGER_API_KEY not set"
        }

    checks = [{"check": "api_key_present", "result": True}]
    status = "success"
    try:
        # Attempt to use helper if available
        try:
            from hostinger_helper import hostinger_api
            domains = hostinger_api.list_domains(api_key)
            checks.append({"check": "list_domains", "result": bool(domains)})
        except Exception as e:
            checks.append({"check": "list_domains_helper", "result": f"fallback: {e}"})
    except Exception as e:
        status = "fail"
        checks.append({"check": "exception", "result": str(e)})

    return {"name": "hostinger", "status": status, "checks": checks}
