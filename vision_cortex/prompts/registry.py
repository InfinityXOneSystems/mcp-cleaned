"""Autonomous Prompt Registry with CLI alias system.

Maps short aliases (e.g., L1_SYSTEM_SCAN) to structured prompt definitions
aligned with AUTONOMOUS_PROMPTS.md levels. Each prompt has:
- id: unique identifier (the alias)
- level: autonomy tier (1-10)
- description: what the prompt does
- execution: "manual", "assisted", "background", "auto"
- confidence_threshold: for auto-execution (L9+)
- agents: Vision Cortex agents this prompt invokes
- tags: for routing/filtering
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

EXECUTION_MODES = ["manual", "assisted", "background", "auto"]


@dataclass
class PromptDefinition:
    id: str
    level: int
    description: str
    execution: str = "manual"
    confidence_threshold: float = 0.85
    agents: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    governance_level: str = "HIGH"
    parameters: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------
# Level 1: Assistive (Manual Control)
# ---------------------------------------------------------
L1_SYSTEM_SCAN = PromptDefinition(
    id="L1_SYSTEM_SCAN",
    level=1,
    description="Perform a comprehensive system health check: gateway, DB, services, logs, disk.",
    execution="manual",
    agents=["crawler", "validator"],
    tags=["health", "diagnostics"],
    governance_level="LOW",
)

L1_DATA_INGEST_REVIEW = PromptDefinition(
    id="L1_DATA_INGEST_REVIEW",
    level=1,
    description="Review pending data ingestion tasks: queue status, sync timestamps, data quality.",
    execution="manual",
    agents=["ingestor", "organizer"],
    tags=["ingest", "queue"],
    governance_level="LOW",
)

# ---------------------------------------------------------
# Level 2: Analytical (Assistive with Reasoning)
# ---------------------------------------------------------
L2_INTELLIGENCE_SYNTHESIS = PromptDefinition(
    id="L2_INTELLIGENCE_SYNTHESIS",
    level=2,
    description="Synthesize intelligence from available data; identify patterns and confidence levels.",
    execution="assisted",
    agents=["crawler", "ingestor", "organizer", "visionary"],
    tags=["intelligence", "synthesis"],
    governance_level="MEDIUM",
)

L2_MARKET_ANALYSIS = PromptDefinition(
    id="L2_MARKET_ANALYSIS",
    level=2,
    description="Analyze current market signals: macro, sentiment, consensus, sector, risk.",
    execution="assisted",
    agents=["crawler", "predictor", "strategist"],
    tags=["market", "analysis"],
    governance_level="MEDIUM",
)

# ---------------------------------------------------------
# Level 3: Predictive (Forecasting with Confidence)
# ---------------------------------------------------------
L3_GENERATE_PREDICTIONS = PromptDefinition(
    id="L3_GENERATE_PREDICTIONS",
    level=3,
    description="Generate forward-looking predictions with confidence intervals; human review required.",
    execution="assisted",
    agents=["predictor", "validator"],
    tags=["prediction", "forecast"],
    governance_level="HIGH",
    confidence_threshold=0.70,
)

L3_SCENARIO_ANALYSIS = PromptDefinition(
    id="L3_SCENARIO_ANALYSIS",
    level=3,
    description="Run what-if scenarios with probability-weighted outcomes.",
    execution="assisted",
    agents=["predictor", "strategist", "validator"],
    tags=["scenario", "simulation"],
    governance_level="HIGH",
)

# ---------------------------------------------------------
# Level 4: Planning (Multi-Step Task Orchestration)
# ---------------------------------------------------------
L4_BUILD_STRATEGY = PromptDefinition(
    id="L4_BUILD_STRATEGY",
    level=4,
    description="Construct multi-step strategy with objectives, execution plan, success metrics, risks.",
    execution="assisted",
    agents=["strategist", "visionary", "ceo", "documentor"],
    tags=["strategy", "planning"],
    governance_level="HIGH",
)

L4_PARALLEL_ANALYSIS = PromptDefinition(
    id="L4_PARALLEL_ANALYSIS",
    level=4,
    description="Execute multiple analyses in parallel: distress scoring, credit intel, macro synthesis.",
    execution="assisted",
    agents=["crawler", "ingestor", "organizer", "predictor", "strategist"],
    tags=["parallel", "analysis"],
    governance_level="HIGH",
)

# ---------------------------------------------------------
# Level 5: Execution Planning (Task Sequencing)
# ---------------------------------------------------------
L5_GENERATE_ACTIONS = PromptDefinition(
    id="L5_GENERATE_ACTIONS",
    level=5,
    description="Generate concrete action steps with priorities, dependencies, and approval gates.",
    execution="assisted",
    agents=["strategist", "ceo", "documentor"],
    tags=["actions", "execution"],
    governance_level="HIGH",
)

# ---------------------------------------------------------
# Level 6: Background Execution (Scheduled Tasks)
# ---------------------------------------------------------
L6_SCHEDULED_INTELLIGENCE = PromptDefinition(
    id="L6_SCHEDULED_INTELLIGENCE",
    level=6,
    description="Continuous background intelligence: hourly ingest, rolling predictions, anomaly detection.",
    execution="background",
    agents=["crawler", "ingestor", "predictor", "validator"],
    tags=["scheduled", "background"],
    governance_level="MEDIUM",
)

L6_LEDGER_UPDATES = PromptDefinition(
    id="L6_LEDGER_UPDATES",
    level=6,
    description="Continuously update decision ledgers: append decisions, scores, sources, audit trail.",
    execution="background",
    agents=["documentor", "validator"],
    tags=["ledger", "audit"],
    governance_level="MEDIUM",
)

# ---------------------------------------------------------
# Level 7: Parallel Orchestration (Distributed Execution)
# ---------------------------------------------------------
L7_DAG_EXECUTION = PromptDefinition(
    id="L7_DAG_EXECUTION",
    level=7,
    description="Execute DAG-based workflows: parallelize independent tasks, handle dependencies, retries.",
    execution="background",
    agents=[
        "crawler",
        "ingestor",
        "organizer",
        "predictor",
        "strategist",
        "validator",
        "documentor",
    ],
    tags=["dag", "orchestration"],
    governance_level="HIGH",
)

L7_ADAPTIVE_RESOURCE_ALLOCATION = PromptDefinition(
    id="L7_ADAPTIVE_RESOURCE_ALLOCATION",
    level=7,
    description="Dynamically allocate compute: monitor queue, spin workers, balance load.",
    execution="background",
    agents=["evolver"],
    tags=["resources", "scaling"],
    governance_level="HIGH",
)

# ---------------------------------------------------------
# Level 8: Self-Optimization (Architecture Improvement)
# ---------------------------------------------------------
L8_DETECT_SCALING_PRESSURE = PromptDefinition(
    id="L8_DETECT_SCALING_PRESSURE",
    level=8,
    description="Monitor system for scaling constraints: latency, queue depth, utilization, bottlenecks.",
    execution="background",
    agents=["evolver", "validator"],
    tags=["scaling", "optimization"],
    governance_level="HIGH",
)

L8_MODULARIZE_ARCHITECTURE = PromptDefinition(
    id="L8_MODULARIZE_ARCHITECTURE",
    level=8,
    description="Auto-refactor architecture: identify coupling, propose module boundaries, refactoring plan.",
    execution="assisted",
    agents=["evolver", "documentor", "ceo"],
    tags=["architecture", "refactor"],
    governance_level="CRITICAL",
)

# ---------------------------------------------------------
# Level 9: Autonomous Prediction (Confidence-Governed)
# ---------------------------------------------------------
L9_AUTO_PREDICT = PromptDefinition(
    id="L9_AUTO_PREDICT",
    level=9,
    description="Autonomous prediction: execute if confidence >85%, flag 70-85%, simulate <70%.",
    execution="auto",
    confidence_threshold=0.85,
    agents=["predictor", "validator", "ceo"],
    tags=["auto", "prediction"],
    governance_level="CRITICAL",
)

L9_PAPER_TRADING = PromptDefinition(
    id="L9_PAPER_TRADING",
    level=9,
    description="Execute paper trading strategies: generate signals, virtual trades, track performance.",
    execution="auto",
    confidence_threshold=0.75,
    agents=["predictor", "strategist", "validator"],
    tags=["paper", "trading"],
    governance_level="HIGH",
)

# ---------------------------------------------------------
# Level 10: Self-Evolving Intelligence (Meta-Learning)
# ---------------------------------------------------------
L10_CONTINUOUS_IMPROVEMENT = PromptDefinition(
    id="L10_CONTINUOUS_IMPROVEMENT",
    level=10,
    description="System self-improvement: track accuracy, propose upgrades, sandbox test, staged deploy.",
    execution="auto",
    confidence_threshold=0.90,
    agents=["evolver", "validator", "documentor", "ceo"],
    tags=["meta", "improvement"],
    governance_level="CRITICAL",
)

L10_CONFIDENCE_ESCALATION = PromptDefinition(
    id="L10_CONFIDENCE_ESCALATION",
    level=10,
    description="Handle uncertainty through escalation: high→execute, medium→review, low→human decision.",
    execution="auto",
    confidence_threshold=0.85,
    agents=["ceo", "validator"],
    tags=["escalation", "confidence"],
    governance_level="CRITICAL",
)

# ---------------------------------------------------------
# Registry / Alias System
# ---------------------------------------------------------
# Core L1-L10 system prompts
CORE_PROMPT_REGISTRY: Dict[str, PromptDefinition] = {
    "L1_SYSTEM_SCAN": L1_SYSTEM_SCAN,
    "L1_DATA_INGEST_REVIEW": L1_DATA_INGEST_REVIEW,
    "L2_INTELLIGENCE_SYNTHESIS": L2_INTELLIGENCE_SYNTHESIS,
    "L2_MARKET_ANALYSIS": L2_MARKET_ANALYSIS,
    "L3_GENERATE_PREDICTIONS": L3_GENERATE_PREDICTIONS,
    "L3_SCENARIO_ANALYSIS": L3_SCENARIO_ANALYSIS,
    "L4_BUILD_STRATEGY": L4_BUILD_STRATEGY,
    "L4_PARALLEL_ANALYSIS": L4_PARALLEL_ANALYSIS,
    "L5_GENERATE_ACTIONS": L5_GENERATE_ACTIONS,
    "L6_SCHEDULED_INTELLIGENCE": L6_SCHEDULED_INTELLIGENCE,
    "L6_LEDGER_UPDATES": L6_LEDGER_UPDATES,
    "L7_DAG_EXECUTION": L7_DAG_EXECUTION,
    "L7_ADAPTIVE_RESOURCE_ALLOCATION": L7_ADAPTIVE_RESOURCE_ALLOCATION,
    "L8_DETECT_SCALING_PRESSURE": L8_DETECT_SCALING_PRESSURE,
    "L8_MODULARIZE_ARCHITECTURE": L8_MODULARIZE_ARCHITECTURE,
    "L9_AUTO_PREDICT": L9_AUTO_PREDICT,
    "L9_PAPER_TRADING": L9_PAPER_TRADING,
    "L10_CONTINUOUS_IMPROVEMENT": L10_CONTINUOUS_IMPROVEMENT,
    "L10_CONFIDENCE_ESCALATION": L10_CONFIDENCE_ESCALATION,
}

# Import domain prompts and merge
try:
    from .domain_registry import DOMAIN_ALIASES, DOMAIN_PROMPT_REGISTRY

    PROMPT_REGISTRY: Dict[str, PromptDefinition] = {
        **CORE_PROMPT_REGISTRY,
        **DOMAIN_PROMPT_REGISTRY,
    }
except ImportError:
    # Fallback if domain_registry not available
    PROMPT_REGISTRY: Dict[str, PromptDefinition] = CORE_PROMPT_REGISTRY
    DOMAIN_ALIASES: Dict[str, str] = {}

# Short aliases for convenience (core L1-L10 + domain aliases)
CORE_ALIASES: Dict[str, str] = {
    "scan": "L1_SYSTEM_SCAN",
    "ingest": "L1_DATA_INGEST_REVIEW",
    "intel": "L2_INTELLIGENCE_SYNTHESIS",
    "market": "L2_MARKET_ANALYSIS",
    "predict": "L3_GENERATE_PREDICTIONS",
    "scenario": "L3_SCENARIO_ANALYSIS",
    "strategy": "L4_BUILD_STRATEGY",
    "parallel": "L4_PARALLEL_ANALYSIS",
    "actions": "L5_GENERATE_ACTIONS",
    "scheduled": "L6_SCHEDULED_INTELLIGENCE",
    "ledger": "L6_LEDGER_UPDATES",
    "dag": "L7_DAG_EXECUTION",
    "resources": "L7_ADAPTIVE_RESOURCE_ALLOCATION",
    "scaling": "L8_DETECT_SCALING_PRESSURE",
    "modularize": "L8_MODULARIZE_ARCHITECTURE",
    "auto": "L9_AUTO_PREDICT",
    "paper": "L9_PAPER_TRADING",
    "improve": "L10_CONTINUOUS_IMPROVEMENT",
    "escalate": "L10_CONFIDENCE_ESCALATION",
}

# Merge core and domain aliases
ALIASES: Dict[str, str] = {**CORE_ALIASES, **DOMAIN_ALIASES}


def resolve_alias(name: str) -> Optional[PromptDefinition]:
    """Resolve alias or direct ID to PromptDefinition."""
    canonical = ALIASES.get(name.lower(), name.upper())
    return PROMPT_REGISTRY.get(canonical)


def list_prompts(
    level: Optional[int] = None, tag: Optional[str] = None
) -> List[PromptDefinition]:
    """List prompts, optionally filtering by level or tag."""
    results = list(PROMPT_REGISTRY.values())
    if level is not None:
        results = [p for p in results if p.level == level]
    if tag:
        results = [p for p in results if tag.lower() in (t.lower() for t in p.tags)]
    return results
