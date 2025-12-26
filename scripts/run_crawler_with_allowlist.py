#!/usr/bin/env python3
"""Wrapper to set SCRAPER_ALLOWED_HOSTS before importing and running the demo.

This ensures the allowlist check in `safety.py` reads the environment variable.
"""
import os
import runpy
import sys

if __name__ == "__main__":
    # Minimal default; can be overridden by environment or callers
    os.environ.setdefault("SCRAPER_ALLOWED_HOSTS", "example.com")
    # Run the existing demo script in-process so imports see the env var
    runpy.run_path("scripts/run_crawler_demo.py", run_name="__main__")
