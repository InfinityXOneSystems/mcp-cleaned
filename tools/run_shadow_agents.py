"""Run a team of 'shadow' crawler agents in parallel as a capability test.

Each shadow agent runs its own `OptimizedCrawler` or `AsyncCrawler` instance
with separate allowed domains/seeds. This script demonstrates parallel
execution using asyncio and shows aggregated results.
"""
import argparse
import asyncio
import json
import os
import sys
from typing import List

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False

try:
    from vision_cortex.instrumentation.observability import PROM_DISPATCH_QUICK, PROM_TASK_LATENCY
except Exception:
    PROM_DISPATCH_QUICK = None
    PROM_TASK_LATENCY = None

try:
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
except Exception:
    tracer = None

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from crawler_optimized import CrawlConfig, OptimizedCrawler, crawl_optimized


async def fetch_with_playwright(url: str, timeout: int = 30000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=timeout)
        content = await page.content()
        await browser.close()
        return content


async def run_shadow_agent(name: str, start_url: str, concurrency: int = 5, max_pages: int = 20, use_playwright: bool = False, no_robots: bool = False):
    cfg = CrawlConfig(max_pages=max_pages, max_concurrent=concurrency, allowed_domains=[start_url.split('/')[2]])
    print(f"[{name}] starting crawl {start_url} (concurrency={concurrency}, max_pages={max_pages})")
    if PROM_DISPATCH_QUICK:
        try:
            PROM_DISPATCH_QUICK.inc()
        except Exception:
            pass

    span = None
    if tracer:
        span = tracer.start_span(f"shadow_agent.{name}")

    try:
        if use_playwright:
            if not PLAYWRIGHT_AVAILABLE:
                raise RuntimeError("Playwright not installed in environment")
            # perform a single Playwright fetch for demonstration
            html = await fetch_with_playwright(start_url)
            print(f"[{name}] playwright fetch length={len(html)}")
            return {"name": name, "result": {"pages_crawled": 1, "start_url": start_url}}

        res = await crawl_optimized(start_url, cfg)
        print(f"[{name}] finished: pages_crawled={res['pages_crawled']}")
        return {"name": name, "result": res}
    except Exception as e:
        print(f"[{name}] error: {e}")
        return {"name": name, "error": str(e)}
    finally:
        if span:
            try:
                span.end()
            except Exception:
                pass


async def run_team(seeds: List[str], concurrency: int = 5, max_pages: int = 20):
    tasks = []
    for i, s in enumerate(seeds):
        tasks.append(run_shadow_agent(f"agent_{i+1}", s, concurrency=concurrency, max_pages=max_pages))
    results = await asyncio.gather(*tasks)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('seeds', nargs='*', help='seed URLs to crawl')
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument('--max-pages', type=int, default=10)
    parser.add_argument('--use-playwright', action='store_true', help='Use Playwright for JS-rendered pages')
    parser.add_argument('--no-robots', action='store_true', help='Ignore robots.txt (requires --dev-ok or ALLOW_NO_ROBOTS=1)')
    parser.add_argument('--dev-ok', action='store_true', help='Acknowledges you are in a dev/testing environment (required to use --no-robots)')
    parser.add_argument('--enable-all-capabilities', action='store_true', help='Enable all optional/testing capabilities (Playwright, tracing, metrics). May attempt to auto-install if --auto-install is provided')
    parser.add_argument('--auto-install', action='store_true', help='If capability packages are missing, attempt to install them automatically (requires network).')
    args = parser.parse_args()

    seeds = args.seeds or ["https://example.com", "https://www.python.org"]

    # Handle enable-all-capabilities convenience
    if args.enable_all_capabilities:
        if not PLAYWRIGHT_AVAILABLE:
            if args.auto_install:
                print("Playwright not found — attempting to install via pip. This requires network access and may take a while.")
                try:
                    import subprocess
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"]) 
                    # Try to run playwright install step
                    try:
                        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"]) 
                    except Exception:
                        # Best-effort; continue even if browser install fails
                        print("Warning: playwright browser install step failed or requires extra privileges. Continue and try manual install if needed.")
                    PLAYWRIGHT_AVAILABLE = True
                except Exception as e:
                    print(f"Auto-install failed: {e}")
                    print("Proceeding without Playwright. If you need Playwright, run: pip install playwright && python -m playwright install")
            else:
                print("Note: Playwright not installed. To enable Playwright pass --auto-install or install manually:")
                print("  pip install playwright")
                print("  python -m playwright install chromium")
        # enable playwright use by default when enabling all capabilities
        args.use_playwright = True

    # Safety gate for --no-robots
    allow_no_robots_env = os.environ.get('ALLOW_NO_ROBOTS', '') == '1'
    if args.no_robots and not (args.dev_ok or allow_no_robots_env):
        print("Refusing to run with --no-robots without explicit dev acknowledgement.")
        print("Either pass --dev-ok or set environment variable ALLOW_NO_ROBOTS=1 for testing in controlled environments.")
        sys.exit(1)

    coro = run_team(seeds, concurrency=args.concurrency, max_pages=args.max_pages, use_playwright=args.use_playwright, no_robots=args.no_robots)
    res = asyncio.run(coro)
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
