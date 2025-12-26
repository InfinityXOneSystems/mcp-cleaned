import asyncio
import json
import os
import time
from pathlib import Path
from typing import List, Dict
import aiofiles
import httpx
from playwright.async_api import async_playwright

RAW_OUT = Path("crawler/output/raw")
RAW_OUT.mkdir(parents=True, exist_ok=True)

async def fetch_robots_txt(url: str, client: httpx.AsyncClient, timeout: int = 10) -> str:
    try:
        r = await client.get(url.rstrip("/") + "/robots.txt", timeout=timeout)
        return r.text
    except Exception:
        return ""

async def allowed_by_robots(url: str, client: httpx.AsyncClient) -> bool:
    # lightweight check; replace with robust parser if needed
    robots = await fetch_robots_txt(url, client)
    return "Disallow: /" not in robots

async def save_snapshot(url: str, html: str, text: str, metadata: Dict):
    ts = int(time.time())
    fname = RAW_OUT / f"{ts}_{abs(hash(url))}.json"
    async with aiofiles.open(fname, "w", encoding="utf-8") as f:
        await f.write(json.dumps({"url": url, "html": html, "text": text, "metadata": metadata}, ensure_ascii=False))

async def crawl_page(playwright, url: str, timeout: int = 60) -> Dict:
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.set_default_navigation_timeout(timeout * 1000)
    await page.goto(url)
    # simple render + text extraction
    html = await page.content()
    text = await page.inner_text("body")
    await browser.close()
    return {"url": url, "html": html, "text": text}

async def crawl_urls(urls: List[str], concurrency: int = 4):
    async with httpx.AsyncClient() as client:
        async with async_playwright() as p:
            sem = asyncio.Semaphore(concurrency)
            async def _crawl(u):
                async with sem:
                    if not await allowed_by_robots(u, client):
                        return
                    try:
                        snap = await crawl_page(p, u)
                        await save_snapshot(u, snap["html"], snap["text"], {"fetched_at": time.time()})
                    except Exception as e:
                        # log minimal error
                        print("crawl error", u, e)
            await asyncio.gather(*( _crawl(u) for u in urls ))

def load_seed(seed_path: str) -> Dict:
    import yaml
    with open(seed_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

async def run_from_seed(seed_file: str):
    seed = load_seed(seed_file)
    urls = [s["url"] for s in seed.get("sources", [])]
    await crawl_urls(urls)

if __name__ == "__main__":
    import sys
    seed = sys.argv[1] if len(sys.argv) > 1 else "crawler/seeds/business_loans.yaml"
    asyncio.run(run_from_seed(seed))
