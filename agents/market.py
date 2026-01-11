import asyncio
import logging

logger = logging.getLogger(__name__)


async def run(cfg):
    while True:
        logger.info("Market: fetching funding signals and news...")
        await asyncio.sleep(120)
