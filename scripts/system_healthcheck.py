#!/usr/bin/env python3
"""Run health checks against local services and report status."""
import json
import os

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SERVICES = {
    "gateway": "http://localhost:8000/health",
    "dashboard": "http://localhost:8001/api/portfolio",
    "intelligence": "http://localhost:8002/health",
    "admin": "http://localhost:8000/admin",
}


def check(url, timeout=2.0):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code, r.text[:200]
    except Exception as e:
        return None, str(e)


def main():
    any_fail = False
    results = {}
    for name, url in SERVICES.items():
        status, body = check(url)
        ok = status is not None and status < 400
        results[name] = {"ok": ok, "status": status, "body": body}
        any_fail = any_fail or not ok
    out = os.path.join(ROOT, "system-health.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Wrote", out)
    for k, v in results.items():
        print(k, "OK" if v["ok"] else "FAIL", v["status"])
    return 0 if not any_fail else 2


if __name__ == "__main__":
    raise SystemExit(main())
