import asyncio
import logging

logger = logging.getLogger(__name__)


async def run(cfg):
    while True:
        logger.info("Predictor: running short-horizon predictions...")
        await asyncio.sleep(240)
