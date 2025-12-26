#!/usr/bin/env python3
"""Run a quick crawl using the repo's crawler and write results to data/reports."""
import sys
import asyncio
import json
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from crawler import crawl


async def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('url', help='Start URL to crawl')
    p.add_argument('--pages', type=int, default=10)
    p.add_argument('--depth', type=int, default=1)
    args = p.parse_args()

    start = time.time()
    print(f"Starting crawl: {args.url} (pages={args.pages}, depth={args.depth})")
    try:
        results = await crawl(args.url, max_pages=args.pages, max_depth=args.depth, delay=0.5, concurrency=3)
    except Exception as e:
        print('Crawl failed:', e)
        raise
    duration = time.time() - start
    out = {
        'start_url': args.url,
        'max_pages': args.pages,
        'max_depth': args.depth,
        'duration_sec': duration,
        'found': len(results),
        'results_summary': [{'url': r.get('url'), 'status': r.get('status')} for r in results[:20]]
    }
    reports = REPO_ROOT / 'data' / 'reports'
    reports.mkdir(parents=True, exist_ok=True)
    fname = reports / f'crawl_report_{int(time.time())}.json'
    fname.write_text(json.dumps(out, indent=2))
    print('Wrote report to', fname)


if __name__ == '__main__':
    asyncio.run(main())
