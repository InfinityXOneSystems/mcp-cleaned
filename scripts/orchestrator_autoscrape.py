#!/usr/bin/env python3
"""Orchestrator to schedule scraping -> ingest -> predict cycles.

This is a minimal orchestrator intended for cloud deployment (cronjob or K8s Job).
"""
import os
import time

import requests

GATEWAY = os.environ.get("GATEWAY_URL", "http://localhost:8000")


def trigger_crawl(url):
    r = requests.post(f"{GATEWAY}/crawl", json={"url": url, "depth": 1}, timeout=10)
    return r.status_code, r.text[:200]


def trigger_ingest(doc):
    r = requests.post(f"{GATEWAY}/ingest", json=doc, timeout=10)
    return r.status_code, r.text[:200]


def trigger_predict(payload):
    r = requests.post(f"{GATEWAY}/predict", json=payload, timeout=10)
    return r.status_code, r.text[:200]


def main():
    # Example target list - replace with production sources or cloud config
    targets = [
        "https://example.com",
    ]
    for t in targets:
        print("Triggering crawl", t)
        print(trigger_crawl(t))
        time.sleep(1)
        print("Triggering predict (demo)")
        print(trigger_predict({"model": "baseline", "input": {"url": t}}))


if __name__ == "__main__":
    main()
