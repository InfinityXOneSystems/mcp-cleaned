#!/usr/bin/env python3
"""Simple auto-heal loop: run healthcheck, attempt remediation stubs.

In cloud, replace remediation with Cloud Run redeploy or alerting.
"""
import json
import os
import subprocess
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_healthcheck():
    cmd = ["python", os.path.join(ROOT, "scripts", "system_healthcheck.py")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    report = None
    try:
        with open(os.path.join(ROOT, "system-health.json"), "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception:
        pass
    return res.returncode, report


def remediate(report):
    # Placeholder: log failing services; in cloud, trigger redeploy or restart.
    if not report:
        print("No report to remediate")
        return
    for name, data in report.items():
        if not data.get("ok"):
            print("Would remediate service:", name)


def main():
    while True:
        code, report = run_healthcheck()
        if code != 0:
            remediate(report)
        time.sleep(int(os.environ.get("AUTO_HEAL_INTERVAL", "60")))


if __name__ == "__main__":
    main()
