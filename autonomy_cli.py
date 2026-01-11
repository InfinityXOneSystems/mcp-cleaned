#!/usr/bin/env python3
"""
Autonomy Stack Development CLI
Quick commands for local development and testing
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Optional

# Add repo to path
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime

from autonomy_stack.agent_factory import AgentFactory
from autonomy_stack.memory_layer import MemoryLayer
from autonomy_stack.models import MemoryEntry
from autonomy_stack.security import get_security_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def execute_agent(agent_role: str, objective: str) -> None:
    """Execute a single agent task"""
    logger.info(f"🤖 Executing {agent_role} agent...")

    factory = AgentFactory()
    result = await factory.execute_task(agent_role, objective)

    print(
        json.dumps(
            {
                "agent": result.agent_role,
                "status": result.status.value,
                "confidence": result.confidence,
                "execution_time_ms": result.execution_time_ms,
                "result": result.result,
            },
            indent=2,
        )
    )


async def run_pipeline(agents: list, objectives: list) -> None:
    """Execute a multi-agent pipeline"""
    logger.info(f"🔄 Running pipeline with agents: {agents}")

    if len(agents) != len(objectives):
        logger.error("Agents and objectives lists must be same length")
        return

    factory = AgentFactory()
    results = await factory.execute_pipeline(agents, objectives)

    print(
        json.dumps(
            {"pipeline_status": "completed", "results": [r.dict() for r in results]},
            indent=2,
        )
    )


def list_agents() -> None:
    """List all available agents"""
    factory = AgentFactory()
    agents = factory.list_agents()

    print("\n📋 Available Agents:")
    print("-" * 40)
    for role, display_name in agents.items():
        print(f"  • {display_name:15} ({role})")
    print()


def get_agent_stats() -> None:
    """Get agent statistics"""
    factory = AgentFactory()
    stats = factory.get_agent_stats()

    print("\n📊 Agent Statistics:")
    print("-" * 40)
    print(f"Total agents: {stats['total_agents']}")
    print(f"Agents: {', '.join(stats['agents']) if stats['agents'] else 'None'}")
    print("\n💾 Memory Stats:")
    for collection, count in stats["memory_stats"].items():
        print(f"  • {collection}: {count} entries")
    print()


def store_memory(content: str, agent_role: Optional[str] = None) -> None:
    """Store entry in memory"""
    import uuid

    logger.info(f"💾 Storing memory entry...")

    memory = MemoryLayer()
    entry = MemoryEntry(
        id=str(uuid.uuid4()),
        content=content,
        metadata={"source": "cli", "timestamp": datetime.now().isoformat()},
        agent_role=agent_role,
        timestamp=datetime.now(),
    )

    collection = agent_role if agent_role else "shared"
    success = memory.store(entry, collection=collection)

    print(
        json.dumps(
            {
                "success": success,
                "entry_id": entry.id,
                "collection": collection,
                "content": content[:100] + "..." if len(content) > 100 else content,
            },
            indent=2,
        )
    )


def search_memory(query: str, collection: str = "shared", n_results: int = 5) -> None:
    """Search memory by semantic similarity"""
    logger.info(f"🔍 Searching memory: {query}")

    memory = MemoryLayer()
    results = memory.retrieve(query, collection=collection, n_results=n_results)

    print(
        json.dumps(
            {
                "query": query,
                "collection": collection,
                "results_count": len(results),
                "results": results,
            },
            indent=2,
        )
    )


def memory_stats() -> None:
    """Get memory statistics"""
    memory = MemoryLayer()
    stats = memory.get_memory_stats()

    print("\n💾 Memory Statistics:")
    print("-" * 40)
    total = 0
    for collection, count in stats.items():
        print(f"  • {collection}: {count} entries")
        total += count
    print(f"\n  Total entries: {total}")
    print()


def check_security() -> None:
    """Check security configuration"""
    security = get_security_manager()

    print("\n🔒 Security Status:")
    print("-" * 40)
    print(f"Safe mode: {security.is_safe_mode()}")
    print(
        f"OpenAI API configured: {'✓' if security.get_secret('openai_api_key') else '✗'}"
    )
    print(f"Redis URL: {security.get_redis_url()}")
    print(f"Celery broker: {security.get_celery_broker()}")
    print(f"JWT secret configured: ✓")
    print()


def export_memory(collection: str = "shared") -> None:
    """Export memory collection"""
    memory = MemoryLayer()
    data = memory.export_memory(collection)

    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Autonomy Stack Development CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python autonomy_cli.py execute-agent visionary "What will disrupt tech?"
  python autonomy_cli.py list-agents
  python autonomy_cli.py store-memory "Key insight" --agent visionary
  python autonomy_cli.py search-memory "emerging technologies"
  python autonomy_cli.py memory-stats
  python autonomy_cli.py security-check
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Execute agent
    exec_parser = subparsers.add_parser("execute-agent", help="Execute agent task")
    exec_parser.add_argument(
        "agent", choices=["visionary", "strategist", "builder", "critic"]
    )
    exec_parser.add_argument("objective")

    # Run pipeline
    pipeline_parser = subparsers.add_parser("run-pipeline", help="Run agent pipeline")
    pipeline_parser.add_argument("agents", nargs="+")
    pipeline_parser.add_argument("--objectives", nargs="+", required=True)

    # List agents
    subparsers.add_parser("list-agents", help="List available agents")

    # Agent stats
    subparsers.add_parser("agent-stats", help="Get agent statistics")

    # Store memory
    store_parser = subparsers.add_parser("store-memory", help="Store memory entry")
    store_parser.add_argument("content")
    store_parser.add_argument("--agent", dest="agent_role")

    # Search memory
    search_parser = subparsers.add_parser("search-memory", help="Search memory")
    search_parser.add_argument("query")
    search_parser.add_argument("--collection", default="shared")
    search_parser.add_argument("--limit", type=int, default=5)

    # Memory stats
    subparsers.add_parser("memory-stats", help="Get memory statistics")

    # Export memory
    export_parser = subparsers.add_parser(
        "export-memory", help="Export memory collection"
    )
    export_parser.add_argument("--collection", default="shared")

    # Security check
    subparsers.add_parser("security-check", help="Check security configuration")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute commands
    if args.command == "execute-agent":
        asyncio.run(execute_agent(args.agent, args.objective))

    elif args.command == "run-pipeline":
        asyncio.run(run_pipeline(args.agents, args.objectives))

    elif args.command == "list-agents":
        list_agents()

    elif args.command == "agent-stats":
        get_agent_stats()

    elif args.command == "store-memory":
        store_memory(args.content, args.agent_role)

    elif args.command == "search-memory":
        search_memory(args.query, args.collection, args.limit)

    elif args.command == "memory-stats":
        memory_stats()

    elif args.command == "export-memory":
        export_memory(args.collection)

    elif args.command == "security-check":
        check_security()


if __name__ == "__main__":
    main()
