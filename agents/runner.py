"""
Agents runner: simple scaffolding to run multiple background agents in parallel.
Each agent is a Python module under `agents/` and should implement `run(loop, cfg)` coroutine.
"""

import asyncio
import importlib
import logging

logger = logging.getLogger(__name__)

AGENTS = [
    "agents.scout",
    "agents.market",
    "agents.architect",
    "agents.devops",
    "agents.memory_curator",
    "agents.predictor",
    "agents.guardian",
]


async def start_agent(mod_name, cfg):
    try:
        mod = importlib.import_module(mod_name)
        if hasattr(mod, "run"):
            logger.info(f"Starting agent {mod_name}")
            await mod.run(cfg)
        else:
            logger.warning(f"Agent {mod_name} has no run()")
    except Exception as e:
        logger.error(f"Agent {mod_name} failed: {e}")


async def main():
    cfg = {}
    tasks = []
    for a in AGENTS:
        # run agents as independent tasks
        t = asyncio.create_task(start_agent(a, cfg))
        tasks.append(t)
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", action="store_true")
    args = parser.parse_args()
    if args.start:
        asyncio.run(main())
    else:
        print("Run with --start to launch agents")
