import asyncio, logging
from pathlib import Path
import json
import time
from memory.helpers import dedupe_and_prepare, write_local_memory
logger = logging.getLogger(__name__)


def scan_local_memory():
    data_dir = Path(__file__).parents[1] / 'data'
    files = list(data_dir.glob('*.json'))
    items = []
    for f in files:
        try:
            with open(f,'r',encoding='utf-8') as fh:
                items.append(json.load(fh))
        except:
            continue
    return items


def prioritize(items):
    # simple heuristic: newest first
    items.sort(key=lambda x: x.get('created_at',''), reverse=True)
    return items


async def run(cfg):
    while True:
        logger.info('Memory Curator: consolidating and pruning memory...')
        items = scan_local_memory()
        pri = prioritize(items)
        # ensure canonical ids and embeddings
        for it in pri[:50]:
            try:
                it = dedupe_and_prepare(it)
                write_local_memory(it)
            except Exception as e:
                logger.debug(f'Memory curator item failed: {e}')
        # optionally sync top items to Firestore if configured
        try:
            from omni_gateway import init_firestore
            client = init_firestore()
            if client:
                col = client.collection('mcp_memory')
                for it in pri[:20]:
                    doc_id = it.get('canonical_id')
                    col.document(doc_id).set(it, merge=True)
                logger.info('Memory Curator: synced top items to Firestore')
        except Exception as e:
            logger.debug(f'Memory Curator Firestore sync skipped: {e}')
        await asyncio.sleep(600)
