import os
import json
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
SEEDS_DIR = os.path.join(DATA_DIR, 'seeds')
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')

def load_seeds() -> Dict[str, Any]:
    seeds = {}
    try:
        for fname in os.listdir(SEEDS_DIR):
            path = os.path.join(SEEDS_DIR, fname)
            if os.path.isfile(path) and fname.lower().endswith('.json'):
                with open(path, 'r', encoding='utf-8') as f:
                    seeds[fname] = json.load(f)
    except FileNotFoundError:
        logger.warning('Seeds dir not found: %s', SEEDS_DIR)
    return seeds


def write_report(name: str, payload: Dict[str, Any]):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = int(time.time())
    out = os.path.join(REPORTS_DIR, f"{name}-{ts}.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    logger.info('Wrote report: %s', out)
    return out
