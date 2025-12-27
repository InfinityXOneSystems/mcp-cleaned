"""Headless team integration: lightweight on-demand headless fetchers.

Provides a small registry of headless agent descriptors and a helper to
perform a safe, polite fetch (httpx fallback). This module intentionally
keeps dependencies minimal so it can run in environments without Playwright.
"""
from __future__ import annotations

import time
import urllib.robotparser
from typing import Dict, List, Optional
import httpx
from dataclasses import dataclass


@dataclass
class HeadlessAgentDesc:
    name: str
    description: str
    capabilities: List[str]


def init_headless_team() -> List[HeadlessAgentDesc]:
    return [
        HeadlessAgentDesc(name="headless_crawler_a", description="Lightweight HTTP fetcher", capabilities=["http"]),
        HeadlessAgentDesc(name="headless_crawler_b", description="Rendered page preview (Playwright optional)", capabilities=["http", "render"]),
        HeadlessAgentDesc(name="headless_crawler_c", description="Fast fetch + metadata extractor", capabilities=["http", "meta"]),
    ]


def allowed_by_robots(url: str, user_agent: str = "MCPHeadlessBot/1.0") -> bool:
    try:
        parsed = httpx.URL(url)
        robots_url = f"{parsed.scheme}://{parsed.host}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # if robots can't be read, be conservative and return False
        return False


def fetch_url(url: str, timeout: int = 15, user_agent: str = "MCPHeadlessBot/1.0") -> Dict:
    result = {
        "url": url,
        "status": "error",
        "http_status": None,
        "content_length": 0,
        "text_excerpt": None,
        "duration_seconds": None,
    }
    start = time.time()
    headers = {"User-Agent": user_agent}
    try:
        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            r = client.get(url)
            result["http_status"] = r.status_code
            result["content_length"] = len(r.content or b"")
            text = r.text or ""
            result["text_excerpt"] = text[:2000]
            result["status"] = "ok" if r.status_code < 400 else "error"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    finally:
        result["duration_seconds"] = time.time() - start
    return result
