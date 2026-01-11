#!/usr/bin/env python3
"""Verify memory gateway and hydrate readiness in local or cloud environment."""
import os

import requests

MEMORY_URL = os.environ.get("MEMORY_URL", "http://localhost:8003/health")
HYDRATE_URL = os.environ.get("HYDRATE_URL", "http://localhost:8003/hydrate")


def main():
    try:
        r = requests.get(MEMORY_URL, timeout=5)
        print("Memory health", r.status_code)
    except Exception as e:
        print("Memory health check failed", e)
    try:
        r = requests.post(HYDRATE_URL, json={"test": True}, timeout=5)
        print("Hydrate endpoint", r.status_code)
    except Exception as e:
        print("Hydrate check failed", e)


if __name__ == "__main__":
    main()
