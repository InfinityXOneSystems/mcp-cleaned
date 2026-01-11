"""CLI entrypoint to trigger Vision Cortex system builds and autonomous prompts.

Usage (examples):
    # Run 3 parallel builds
    python -m vision_cortex.cli_auto --runs 3 --governance HIGH

    # Execute a prompt by alias
    python -m vision_cortex.cli_auto --prompt scan
    python -m vision_cortex.cli_auto --prompt brand
    python -m vision_cortex.cli_auto --prompt L2_MARKET_ANALYSIS --confidence 0.8

    # List available prompts
    python -m vision_cortex.cli_auto --list
    python -m vision_cortex.cli_auto --list --level 3
    python -m vision_cortex.cli_auto --list --tag prediction
    python -m vision_cortex.cli_auto --list --category business
    python -m vision_cortex.cli_auto --list --category system

    # List categories
    python -m vision_cortex.cli_auto --categories
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from vision_cortex.comms.message_bus import MessageBus
from vision_cortex.memory.memory_registry import build_memory_registry
from vision_cortex.pipelines.system_build import SystemBuildOrchestrator
from vision_cortex.prompts import ALIASES, list_prompts
from vision_cortex.prompts.executor import PromptExecutor

# Try to import domain-specific utilities
try:
    from vision_cortex.prompts.domain_registry import (
        get_domain_categories,
        list_domain_prompts,
    )

    HAS_DOMAIN = True
except ImportError:
    HAS_DOMAIN = False

    def get_domain_categories() -> List[str]:
        return []

    def list_domain_prompts(**kwargs) -> List[Any]:
        return []


def print_prompt_table(prompts: List[Any]) -> None:
    """Pretty-print prompt definitions."""
    print(f"{'ALIAS':<14} {'ID':<28} {'LVL':>3} {'GOV':<8} {'EXEC':<10} {'TAGS'}")
    print("-" * 90)
    reverse_alias = {v: k for k, v in ALIASES.items()}
    for p in sorted(prompts, key=lambda x: (x.level, x.id)):
        alias = reverse_alias.get(p.id, "")
        tags = ", ".join(p.tags[:3])
        gov = p.governance_level[:6] if hasattr(p, "governance_level") else "N/A"
        print(f"{alias:<14} {p.id:<28} {p.level:>3} {gov:<8} {p.execution:<10} {tags}")


def print_categories() -> None:
    """Print available prompt categories."""
    categories = get_domain_categories()
    core_categories = ["L1-L10 (core system levels)"]
    print("Available prompt categories:")
    print("-" * 40)
    for cat in core_categories + categories:
        print(f"  • {cat}")
    print(f"\nTotal: {len(categories) + len(core_categories)} categories")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Vision Cortex Auto-Build & Prompt CLI"
    )
    parser.add_argument(
        "--runs", type=int, default=1, help="Number of builds to run in parallel"
    )
    parser.add_argument(
        "--governance",
        type=str,
        default="HIGH",
        help="Governance level (LOW|MEDIUM|HIGH|CRITICAL)",
    )
    parser.add_argument("--seed", type=str, default="{}", help="JSON seed payload")
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        help="Execute prompt by alias or ID (e.g., scan, brand, L2_MARKET_ANALYSIS)",
    )
    parser.add_argument(
        "--confidence",
        "-c",
        type=float,
        default=0.75,
        help="Confidence level for prompt execution",
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available prompts"
    )
    parser.add_argument("--level", type=int, help="Filter prompts by level (1-10)")
    parser.add_argument("--tag", type=str, help="Filter prompts by tag")
    parser.add_argument(
        "--category",
        type=str,
        help="Filter prompts by category (business, system, personal, docs, analysis, workflow, governance, special)",
    )
    parser.add_argument(
        "--categories", action="store_true", help="List available prompt categories"
    )
    args = parser.parse_args(argv)

    # Categories mode
    if args.categories:
        print_categories()
        return 0

    # List mode
    if args.list:
        # Combine core and domain prompts
        prompts = list_prompts(level=args.level, tag=args.tag)

        # Filter by category if specified
        if args.category:
            prompts = [
                p
                for p in prompts
                if args.category.lower() in (t.lower() for t in p.tags)
            ]

        if not prompts:
            print("No prompts found matching criteria.")
            return 0
        print(f"Found {len(prompts)} prompts:\n")
        print_prompt_table(prompts)
        return 0

    bus = MessageBus()
    memory = build_memory_registry()

    # Prompt execution mode
    if args.prompt:
        executor = PromptExecutor(bus=bus, memory=memory)
        try:
            params = json.loads(args.seed) if args.seed != "{}" else None
        except json.JSONDecodeError:
            params = None
        result = executor.execute(
            args.prompt, params=params, confidence=args.confidence
        )
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("status") != "error" else 1

    # Build mode (original behavior)
    orchestrator = SystemBuildOrchestrator(
        bus=bus, memory=memory, governance_level=args.governance
    )

    try:
        seed_payload = json.loads(args.seed)
    except json.JSONDecodeError:
        print("Invalid JSON seed", file=sys.stderr)
        return 1

    seeds: List[Dict[str, Any]] = []
    for _ in range(args.runs):
        seeds.append({**seed_payload, "session_id": str(uuid.uuid4())})

    # Run builds in parallel using ThreadPoolExecutor
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(args.runs, 4)) as pool:
        futures = {pool.submit(orchestrator.run_build, seed): seed for seed in seeds}
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                print(json.dumps(result, indent=2, default=str))
            except Exception as exc:
                print(f"Build failed: {exc}", file=sys.stderr)

    print(f"Completed {len(results)} build(s) at {time.time():.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
