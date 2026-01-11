"""
Integration script to verify all autonomy stack components
Run this to validate your setup
"""

import asyncio
import os
import sys
from pathlib import Path

# Add repo to path
sys.path.insert(0, os.path.dirname(__file__))


async def verify_components():
    """Verify all autonomy stack components"""
    print("\n" + "=" * 60)
    print("🤖 AUTONOMY STACK COMPONENT VERIFICATION")
    print("=" * 60 + "\n")

    results = {"components": {}, "summary": {}}

    # 1. Check imports
    print("📦 Checking imports...")
    try:
        from autonomy_stack import (
            AgentConfig,
            AgentFactory,
            MemoryEntry,
            MemoryLayer,
            SecurityManager,
            TaskRequest,
        )

        print("  ✓ Core imports successful")
        results["components"]["imports"] = True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        results["components"]["imports"] = False
        return results

    # 2. Agent Factory
    print("\n🤖 Testing Agent Factory...")
    try:
        factory = AgentFactory()
        agents = factory.list_agents()
        print(f"  ✓ Agent factory created")
        print(f"  ✓ Available agents: {list(agents.keys())}")
        results["components"]["agent_factory"] = True
    except Exception as e:
        print(f"  ✗ Agent factory failed: {e}")
        results["components"]["agent_factory"] = False

    # 3. Memory Layer
    print("\n💾 Testing Memory Layer...")
    try:
        memory = MemoryLayer()
        stats = memory.get_memory_stats()
        print(f"  ✓ Memory layer initialized")
        print(f"  ✓ Collections: {list(stats.keys())}")
        results["components"]["memory_layer"] = True
    except Exception as e:
        print(f"  ✗ Memory layer failed: {e}")
        results["components"]["memory_layer"] = False

    # 4. Security Manager
    print("\n🔒 Testing Security Manager...")
    try:
        security = SecurityManager()
        safe_mode = security.is_safe_mode()
        print(f"  ✓ Security manager initialized")
        print(f"  ✓ Safe mode: {safe_mode}")
        results["components"]["security"] = True
    except Exception as e:
        print(f"  ✗ Security manager failed: {e}")
        results["components"]["security"] = False

    # 5. Agent Execution
    print("\n⚡ Testing Agent Execution...")
    try:
        result = await factory.execute_task("visionary", "Test objective")
        print(f"  ✓ Agent executed successfully")
        print(f"  ✓ Status: {result.status.value}")
        print(f"  ✓ Confidence: {result.confidence}")
        print(f"  ✓ Execution time: {result.execution_time_ms}ms")
        results["components"]["agent_execution"] = True
    except Exception as e:
        print(f"  ✗ Agent execution failed: {e}")
        results["components"]["agent_execution"] = False

    # 6. Memory Operations
    print("\n💾 Testing Memory Operations...")
    try:
        import uuid
        from datetime import datetime

        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content="Test memory entry",
            metadata={"test": True},
            timestamp=datetime.now(),
        )
        success = memory.store(entry)
        print(f"  ✓ Memory storage: {success}")

        results_list = memory.retrieve("test", n_results=1)
        print(f"  ✓ Memory retrieval: {len(results_list)} results")
        results["components"]["memory_operations"] = True
    except Exception as e:
        print(f"  ✗ Memory operations failed: {e}")
        results["components"]["memory_operations"] = False

    # 7. Models
    print("\n📊 Testing Models...")
    try:
        config = AgentConfig(role="visionary")
        request = TaskRequest(
            task_type="test", agent_role="visionary", objective="Test"
        )
        print(f"  ✓ Models instantiated")
        print(f"  ✓ AgentConfig: {config.role}")
        print(f"  ✓ TaskRequest: {request.task_type}")
        results["components"]["models"] = True
    except Exception as e:
        print(f"  ✗ Models failed: {e}")
        results["components"]["models"] = False

    # 8. File Structure
    print("\n📁 Checking File Structure...")
    required_files = [
        "autonomy_stack/__init__.py",
        "autonomy_stack/agent_factory.py",
        "autonomy_stack/memory_layer.py",
        "autonomy_stack/task_queue.py",
        "autonomy_stack/security.py",
        "autonomy_stack/models.py",
        "autonomy_stack/endpoints.py",
        "autonomy_stack/vscode_integration.py",
        "autonomy_gateway.py",
        "autonomy_cli.py",
        "docker-compose.yml",
        "Dockerfile",
        "Dockerfile.celery",
        "requirements_autonomy_stack.txt",
        ".env.template",
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if not missing:
        print("  ✓ All required files present")
        results["components"]["file_structure"] = True
    else:
        print(f"  ✗ Missing files: {missing}")
        results["components"]["file_structure"] = False

    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)

    total = len(results["components"])
    passed = sum(1 for v in results["components"].values() if v)

    for component, status in results["components"].items():
        status_str = "✓" if status else "✗"
        print(f"  {status_str} {component}")

    print(f"\n  Total: {passed}/{total} components verified")

    if passed == total:
        print("\n🎉 ALL COMPONENTS VERIFIED - READY TO USE!")
    else:
        print(f"\n⚠️  {total - passed} component(s) need attention")

    return results


def print_quick_start():
    """Print quick start guide"""
    print("\n" + "=" * 60)
    print("🚀 QUICK START GUIDE")
    print("=" * 60 + "\n")

    print(
        """
1. Configure environment:
   cp .env.template .env
   # Edit .env with your API keys

2. Start services:
   docker-compose up -d

3. Verify services:
   curl http://localhost:8000/health

4. Test API:
   curl -H "X-API-Key: INVESTORS-DEMO-KEY-2025" \\
     http://localhost:8000/autonomy/agents

5. View dashboard:
   open http://localhost:8000

6. Monitor tasks:
   open http://localhost:5555

7. Check metrics:
   open http://localhost:9090

See AUTONOMY_STACK_GUIDE.md for full documentation.
    """
    )


async def main():
    """Main verification routine"""
    try:
        results = await verify_components()
        print_quick_start()

        # Return exit code
        all_passed = all(results["components"].values())
        return 0 if all_passed else 1

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
