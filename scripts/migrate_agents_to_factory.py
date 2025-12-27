"""Migration helper: create AgentFactory instances for agents currently
registered in SmartRouter. This is a best-effort scaffolding helper and
should be adapted per your persistence and config needs.
"""
import sys
import os
import json

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from vision_cortex.integration.agent_integration import init_agents

try:
    from autonomy_stack.agent_factory import AgentFactory, AgentConfig
except Exception:
    AgentFactory = None


def main():
    router = init_agents()
    agents = getattr(router, '_agents', {})
    print(f"Found {len(agents)} agents in SmartRouter: {list(agents.keys())}")

    if not AgentFactory:
        print("AgentFactory not available in environment. Install or add autonomy_stack module.")
        return

    factory = AgentFactory()
    migrated = []
    for role, agent in agents.items():
        cfg = AgentConfig(role=role)
        inst = factory.create_agent_instance(cfg)
        migrated.append(inst)

    print("Migrated instances:")
    print(json.dumps(migrated, default=str, indent=2))


if __name__ == '__main__':
    main()
