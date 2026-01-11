import asyncio
import logging
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


def scan_repo():
    root = Path(__file__).parents[1]
    files = list(root.glob("**/*.py"))
    # return small summary
    return {"file_count": len(files), "sample": str(files[0]) if files else ""}


def fetch_url(url: str) -> str:
    try:
        r = requests.get(url, timeout=5)
        return r.text[:2000]
    except Exception as e:
        logger.debug(f"fetch_url failed: {e}")
        return ""


async def run(cfg):
    while True:
        logger.info("Scout: scanning repo and web for signals...")
        repo_summary = scan_repo()
        # simple external pulse
        pulse = fetch_url("https://news.ycombinator.com/")
        # write to local memory store
        try:
            from memory.helpers import dedupe_and_prepare, write_local_memory

            doc = {
                "type": "scout_snapshot",
                "content": {"repo": repo_summary, "pulse": pulse[:500]},
                "created": datetime.utcnow().isoformat(),
            }
            doc = dedupe_and_prepare(doc)
            cid = write_local_memory(doc)
            logger.info(f"Scout: wrote snapshot {cid}")
        except Exception as e:
            logger.debug(f"Scout memory write failed: {e}")
        await asyncio.sleep(60)
