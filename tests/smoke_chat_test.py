"""Smoke test: import agent integration, init router, and dispatch a test intent.

Run with: python tests/smoke_chat_test.py
"""

import json
import os
import sys
import traceback

# Ensure repo root is on sys.path for local imports
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from vision_cortex.agents.base_agent import AgentContext
from vision_cortex.integration.agent_integration import init_agents


def main():
    try:
        router = init_agents()
        ctx = AgentContext(
            session_id="smoke1", task_id="smoke1", governance_level="LOW"
        )
        payload = {
            "context": ctx,
            "data": {
                "seed": {
                    "sources": [
                        {
                            "url": "https://example.com",
                            "title": "Example",
                            "content": "Example content for smoke test.",
                        }
                    ]
                }
            },
        }

        print("Dispatching 'discover' intent to router...")
        result = router.dispatch("discover", payload)
        print("Result:")
        try:
            print(json.dumps(result, default=str, indent=2))
        except Exception:
            print(repr(result))

    except Exception:
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
