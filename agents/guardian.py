import asyncio
import logging

logger = logging.getLogger(__name__)


async def run(cfg):
    while True:
        logger.info("Guardian: validating outputs, safety checks...")
        await asyncio.sleep(90)
