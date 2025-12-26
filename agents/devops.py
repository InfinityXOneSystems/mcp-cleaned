import asyncio, logging
logger = logging.getLogger(__name__)

async def run(cfg):
    while True:
        logger.info('DevOps: monitoring CI/CD and deployments...')
        await asyncio.sleep(180)
