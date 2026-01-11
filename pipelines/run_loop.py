import asyncio
import logging
import time

from pipelines.ingest import load_seeds, write_report

logger = logging.getLogger("run_loop")


async def run_cycle():
    logger.info("Cycle start")
    seeds = load_seeds()
    # For demo purposes: create a simple report summarizing seeds
    report = {
        "ts": int(time.time()),
        "seed_count": len(seeds),
        "seeds": list(seeds.keys()),
    }
    out = write_report("cycle_summary", report)
    logger.info("Cycle complete, report=%s", out)


async def main_loop(interval_seconds: int = 3600):
    logger.info("Starting run loop with interval=%s seconds", interval_seconds)
    while True:
        try:
            await run_cycle()
        except Exception as e:
            logger.exception("Run cycle failed: %s", e)
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
    asyncio.run(main_loop(interval))
