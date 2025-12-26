import asyncio, logging
logger = logging.getLogger(__name__)

async def run(cfg):
    while True:
        logger.info('Architect: reviewing system topology and drift...')
        await asyncio.sleep(300)
