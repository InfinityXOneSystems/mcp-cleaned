"""Domain-Specific Autonomous Prompt Registry.

These prompts are extracted from the auto-prompts folder containing 59 specialized
automation prompts for business, personal, and system operations. They extend the
core L1-L10 system prompts with domain-specific capabilities.

Categories:
- SYSTEM: Core system operations (Auto All, Auto Build, Auto Fix, Auto Heal, etc.)
- BUSINESS: Business operations (Auto Brand, Auto Budget, Auto Marketing, etc.)
- PERSONAL: Personal development (Auto Personal, Auto Passion, etc.)
- DOCS: Documentation (Auto Doc Create, Auto Doc Evolve, Auto Doc Transform)
- ANALYSIS: Analysis capabilities (Auto Gap, Auto Competition, Auto Market, etc.)
- WORKFLOW: Workflow automation (Auto Workflow, Auto Orchestrator, etc.)
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .registry import PromptDefinition

# =============================================================================
# SYSTEM DOMAIN PROMPTS
# =============================================================================
AUTO_ALL = PromptDefinition(
    id="AUTO_ALL",
    level=6,
    description="Autonomous Backend Engineering Orchestrator: Discover → Analyze → Plan → Act → Validate → Log → Propose Next → Repeat across code, infra, automations, docs, repos, and AI configuration.",
    execution="background",
    agents=[
        "crawler",
        "ingestor",
        "organizer",
        "predictor",
        "strategist",
        "validator",
        "documentor",
        "evolver",
    ],
    tags=["system", "orchestration", "auto"],
    governance_level="HIGH",
)

AUTO_BUILD = PromptDefinition(
    id="AUTO_BUILD",
    level=5,
    description="Autonomous Builder: Design → Scaffold → Implement → Test → Document → Wire features into architecture with strong safety and reviewability.",
    execution="assisted",
    agents=["strategist", "documentor", "validator"],
    tags=["system", "build", "development"],
    governance_level="HIGH",
)

AUTO_DIAGNOSE = PromptDefinition(
    id="AUTO_DIAGNOSE",
    level=4,
    description="Autonomous Diagnostic + SRE Engineer: Scan, gather signals, detect problems, classify priorities, propose safe next actions.",
    execution="assisted",
    agents=["crawler", "validator", "evolver"],
    tags=["system", "diagnostics", "sre"],
    governance_level="MEDIUM",
)

AUTO_FIX = PromptDefinition(
    id="AUTO_FIX",
    level=5,
    description="Autonomous Bugfix + Error-Clearing: Take errors/failures, identify root causes, apply minimal targeted fixes, validate, leave system strictly better.",
    execution="assisted",
    agents=["validator", "evolver"],
    tags=["system", "fix", "debug"],
    governance_level="HIGH",
)

AUTO_HEAL = PromptDefinition(
    id="AUTO_HEAL",
    level=6,
    description="Autonomous Healing: Stability, resilience, robustness, design improvements beyond simple fixes.",
    execution="background",
    agents=["evolver", "validator", "strategist"],
    tags=["system", "heal", "resilience"],
    governance_level="HIGH",
)

AUTO_EVOLVE = PromptDefinition(
    id="AUTO_EVOLVE",
    level=7,
    description="Self-Evolution Engine: Analyze state, detect gaps, propose evolution steps, design experiments, learn from results.",
    execution="background",
    agents=["evolver", "strategist", "visionary", "ceo"],
    tags=["system", "evolution", "meta"],
    governance_level="CRITICAL",
)

AUTO_SYNC = PromptDefinition(
    id="AUTO_SYNC",
    level=5,
    description="Synchronization Engine: Align docs, UI, prompts, external messaging with actual functionality.",
    execution="assisted",
    agents=["documentor", "validator"],
    tags=["system", "sync", "alignment"],
    governance_level="MEDIUM",
)

AUTO_VALIDATE = PromptDefinition(
    id="AUTO_VALIDATE",
    level=4,
    description="Validation Engine: Check messaging accuracy, safety, compliance, and alignment with product reality.",
    execution="assisted",
    agents=["validator"],
    tags=["system", "validation", "safety"],
    governance_level="HIGH",
)

AUTO_PARALLEL = PromptDefinition(
    id="AUTO_PARALLEL",
    level=6,
    description="Parallel Execution Engine: Support simultaneous exploration of multiple concepts, then selection.",
    execution="background",
    agents=["crawler", "predictor", "strategist"],
    tags=["system", "parallel", "exploration"],
    governance_level="MEDIUM",
)

AUTO_ORCHESTRATOR = PromptDefinition(
    id="AUTO_ORCHESTRATOR",
    level=7,
    description="Meta Orchestrator: Coordinate multiple AUTO-* modules, manage dependencies, optimize execution order.",
    execution="background",
    agents=["ceo", "strategist", "evolver"],
    tags=["system", "orchestration", "meta"],
    governance_level="CRITICAL",
)

AUTO_MAINTAIN = PromptDefinition(
    id="AUTO_MAINTAIN",
    level=5,
    description="Maintenance Engine: Continuous upkeep, cleanup, optimization of system health.",
    execution="background",
    agents=["validator", "evolver"],
    tags=["system", "maintenance", "ops"],
    governance_level="MEDIUM",
)

AUTO_SANDBOX = PromptDefinition(
    id="AUTO_SANDBOX",
    level=5,
    description="Sandbox Testing: Safe experimentation environment for new features and risky changes.",
    execution="assisted",
    agents=["validator", "evolver"],
    tags=["system", "sandbox", "testing"],
    governance_level="HIGH",
)

AUTO_PRODUCTION = PromptDefinition(
    id="AUTO_PRODUCTION",
    level=7,
    description="Production Deployment: Safe production deployment with rollback, monitoring, staged rollout.",
    execution="assisted",
    agents=["validator", "evolver", "ceo"],
    tags=["system", "production", "deployment"],
    governance_level="CRITICAL",
)

AUTO_MIRROR = PromptDefinition(
    id="AUTO_MIRROR",
    level=4,
    description="Mirror Engine: Keep systems synchronized across environments, repos, platforms.",
    execution="background",
    agents=["crawler", "validator"],
    tags=["system", "mirror", "sync"],
    governance_level="MEDIUM",
)

AUTO_INDEXER = PromptDefinition(
    id="AUTO_INDEXER",
    level=4,
    description="Indexing Engine: Build and maintain searchable indexes across all system content.",
    execution="background",
    agents=["ingestor", "organizer"],
    tags=["system", "index", "search"],
    governance_level="LOW",
)

AUTO_INGEST = PromptDefinition(
    id="AUTO_INGEST",
    level=4,
    description="Data Ingestion: Continuous intake, normalization, and processing of external data sources.",
    execution="background",
    agents=["crawler", "ingestor"],
    tags=["system", "ingest", "data"],
    governance_level="MEDIUM",
)

AUTO_COMPILE = PromptDefinition(
    id="AUTO_COMPILE",
    level=4,
    description="Universal Parser & Compiler: Take raw input (threads, pages, docs) and compile into structured knowledge.",
    execution="assisted",
    agents=["ingestor", "organizer", "documentor"],
    tags=["system", "compile", "parse"],
    governance_level="MEDIUM",
)

AUTO_GOOGLE = PromptDefinition(
    id="AUTO_GOOGLE",
    level=5,
    description="Google Ops OS: Deep integration with Google Workspace/Cloud, mirror systems to Drive/Docs/Sheets.",
    execution="assisted",
    agents=["crawler", "documentor", "validator"],
    tags=["system", "google", "integration"],
    governance_level="HIGH",
)


# =============================================================================
# BUSINESS DOMAIN PROMPTS
# =============================================================================
AUTO_BRAND = PromptDefinition(
    id="AUTO_BRAND",
    level=4,
    description="Global Brand Architect: Build Brand OS - identity, story, voice, visuals, promises across all touchpoints.",
    execution="assisted",
    agents=["visionary", "strategist", "documentor"],
    tags=["business", "brand", "marketing"],
    governance_level="MEDIUM",
)

AUTO_BUDGET = PromptDefinition(
    id="AUTO_BUDGET",
    level=4,
    description="Financial Scenario Planner: Turn income/expense ideas into models, budgets, runway scenarios, risk analysis.",
    execution="assisted",
    agents=["predictor", "strategist"],
    tags=["business", "finance", "budget"],
    governance_level="HIGH",
)

AUTO_MARKETING = PromptDefinition(
    id="AUTO_MARKETING",
    level=4,
    description="Marketing Engine: Channels, campaigns, funnels, messaging experiments, audience targeting.",
    execution="assisted",
    agents=["strategist", "visionary", "documentor"],
    tags=["business", "marketing", "growth"],
    governance_level="MEDIUM",
)

AUTO_MARKET_ANALYSIS = PromptDefinition(
    id="AUTO_MARKET_ANALYSIS",
    level=4,
    description="Market Intelligence: Analyze market trends, opportunities, threats, competitive landscape.",
    execution="assisted",
    agents=["crawler", "predictor", "strategist"],
    tags=["business", "market", "analysis"],
    governance_level="MEDIUM",
)

AUTO_COMPETITION = PromptDefinition(
    id="AUTO_COMPETITION",
    level=4,
    description="Competitor Analysis & Market Mapping: Understand landscape, compare offerings, derive strategic opportunities.",
    execution="assisted",
    agents=["crawler", "predictor", "strategist"],
    tags=["business", "competition", "analysis"],
    governance_level="MEDIUM",
)

AUTO_MONEY_MAKER = PromptDefinition(
    id="AUTO_MONEY_MAKER",
    level=5,
    description="Revenue Generation: Identify and develop offers, revenue streams, monetization strategies.",
    execution="assisted",
    agents=["strategist", "visionary", "predictor"],
    tags=["business", "revenue", "monetization"],
    governance_level="HIGH",
)

AUTO_MVP = PromptDefinition(
    id="AUTO_MVP",
    level=5,
    description="MVP Builder: Rapid minimum viable product design, validation, and iteration framework.",
    execution="assisted",
    agents=["strategist", "validator", "documentor"],
    tags=["business", "mvp", "product"],
    governance_level="MEDIUM",
)

AUTO_NAME = PromptDefinition(
    id="AUTO_NAME",
    level=3,
    description="Naming Engine: Generate and validate names for products, features, companies, brands.",
    execution="assisted",
    agents=["visionary", "validator"],
    tags=["business", "naming", "brand"],
    governance_level="LOW",
)

AUTO_NICHE_FINDER = PromptDefinition(
    id="AUTO_NICHE_FINDER",
    level=4,
    description="Niche Discovery: Identify underserved markets, untapped opportunities, positioning angles.",
    execution="assisted",
    agents=["crawler", "predictor", "strategist"],
    tags=["business", "niche", "market"],
    governance_level="MEDIUM",
)

AUTO_VIRAL = PromptDefinition(
    id="AUTO_VIRAL",
    level=4,
    description="Viral Growth Engine: Design viral loops, referral mechanics, network effects.",
    execution="assisted",
    agents=["strategist", "visionary"],
    tags=["business", "viral", "growth"],
    governance_level="MEDIUM",
)

AUTO_WEBSITE = PromptDefinition(
    id="AUTO_WEBSITE",
    level=4,
    description="Website Builder: Design and structure websites for conversion, clarity, and brand alignment.",
    execution="assisted",
    agents=["visionary", "documentor", "validator"],
    tags=["business", "website", "frontend"],
    governance_level="MEDIUM",
)

AUTO_SOCIAL = PromptDefinition(
    id="AUTO_SOCIAL",
    level=4,
    description="Social Media Engine: Content strategy, posting cadence, engagement, audience growth.",
    execution="assisted",
    agents=["strategist", "documentor"],
    tags=["business", "social", "marketing"],
    governance_level="MEDIUM",
)

AUTO_LOGO = PromptDefinition(
    id="AUTO_LOGO",
    level=3,
    description="Logo & Visual Identity: Generate logo concepts, visual direction, brand asset guidelines.",
    execution="assisted",
    agents=["visionary"],
    tags=["business", "logo", "brand"],
    governance_level="LOW",
)

AUTO_OPEN_SOURCE = PromptDefinition(
    id="AUTO_OPEN_SOURCE",
    level=4,
    description="Open Source Strategy: Design OSS projects, community building, contribution guidelines.",
    execution="assisted",
    agents=["strategist", "documentor"],
    tags=["business", "opensource", "community"],
    governance_level="MEDIUM",
)

AUTO_ENTERPRISE = PromptDefinition(
    id="AUTO_ENTERPRISE",
    level=6,
    description="Enterprise Evolution Architect: Evolve production systems into enterprise-grade platforms (security, compliance, scale).",
    execution="assisted",
    agents=["strategist", "validator", "ceo"],
    tags=["business", "enterprise", "scale"],
    governance_level="CRITICAL",
)


# =============================================================================
# PERSONAL DOMAIN PROMPTS
# =============================================================================
AUTO_PERSONAL = PromptDefinition(
    id="AUTO_PERSONAL",
    level=3,
    description="Personal Development Engine: Life goals, habits, skills, energy management, personal OS.",
    execution="assisted",
    agents=["strategist", "visionary"],
    tags=["personal", "development", "life"],
    governance_level="LOW",
)

AUTO_PASSION = PromptDefinition(
    id="AUTO_PASSION",
    level=3,
    description="Passion Discovery: Identify core interests, values, motivations, and alignment paths.",
    execution="assisted",
    agents=["visionary", "strategist"],
    tags=["personal", "passion", "purpose"],
    governance_level="LOW",
)

AUTO_FREE = PromptDefinition(
    id="AUTO_FREE",
    level=3,
    description="Zero-Cost Architect: Maximize free/no-cost options first, leverage existing assets.",
    execution="assisted",
    agents=["strategist", "predictor"],
    tags=["personal", "free", "budget"],
    governance_level="LOW",
)


# =============================================================================
# DOCUMENTATION DOMAIN PROMPTS
# =============================================================================
AUTO_DOC_CREATE = PromptDefinition(
    id="AUTO_DOC_CREATE",
    level=4,
    description="Documentation Creator: Turn systems, repos, workflows into clear, structured, maintainable docs.",
    execution="assisted",
    agents=["documentor", "validator"],
    tags=["docs", "create", "knowledge"],
    governance_level="MEDIUM",
)

AUTO_DOC_EVOLVE = PromptDefinition(
    id="AUTO_DOC_EVOLVE",
    level=5,
    description="Document Evolution Engine: Living documentation system that evolves in real-time with code/architecture.",
    execution="background",
    agents=["documentor", "evolver"],
    tags=["docs", "evolve", "living"],
    governance_level="MEDIUM",
)

AUTO_DOC_TRANSFORM = PromptDefinition(
    id="AUTO_DOC_TRANSFORM",
    level=4,
    description="Doc Transformer: Convert raw content into structured, Doc-Evolver-ready artifacts.",
    execution="assisted",
    agents=["ingestor", "documentor"],
    tags=["docs", "transform", "parse"],
    governance_level="MEDIUM",
)


# =============================================================================
# ANALYSIS DOMAIN PROMPTS
# =============================================================================
AUTO_GAP_ANALYZER = PromptDefinition(
    id="AUTO_GAP_ANALYZER",
    level=4,
    description="Gap Analyzer: Take any artifact and identify what's missing to make it exceptional.",
    execution="assisted",
    agents=["validator", "strategist"],
    tags=["analysis", "gap", "improvement"],
    governance_level="MEDIUM",
)

AUTO_CONSENSUS = PromptDefinition(
    id="AUTO_CONSENSUS",
    level=5,
    description="Consensus Engine: Take multiple answers/sources and produce one coherent, well-reasoned conclusion.",
    execution="assisted",
    agents=["predictor", "validator", "ceo"],
    tags=["analysis", "consensus", "decision"],
    governance_level="HIGH",
)

AUTO_PREDICTOR = PromptDefinition(
    id="AUTO_PREDICTOR",
    level=5,
    description="Prediction Engine: Generate forward-looking forecasts with confidence intervals.",
    execution="assisted",
    agents=["predictor", "validator"],
    tags=["analysis", "prediction", "forecast"],
    governance_level="HIGH",
)

AUTO_TREND = PromptDefinition(
    id="AUTO_TREND",
    level=4,
    description="Trend Analysis: Identify emerging trends, patterns, and early signals.",
    execution="assisted",
    agents=["crawler", "predictor"],
    tags=["analysis", "trends", "signals"],
    governance_level="MEDIUM",
)

AUTO_TOP_5 = PromptDefinition(
    id="AUTO_TOP_5",
    level=3,
    description="Top 5 Generator: Quickly identify and rank top priorities, options, or recommendations.",
    execution="assisted",
    agents=["strategist", "predictor"],
    tags=["analysis", "ranking", "priorities"],
    governance_level="LOW",
)


# =============================================================================
# WORKFLOW DOMAIN PROMPTS
# =============================================================================
AUTO_WORKFLOW = PromptDefinition(
    id="AUTO_WORKFLOW",
    level=5,
    description="Workflow Engine: Design, optimize, and automate recurring workflows and processes.",
    execution="assisted",
    agents=["strategist", "evolver"],
    tags=["workflow", "automation", "process"],
    governance_level="MEDIUM",
)

AUTO_PLAN_EXECUTE = PromptDefinition(
    id="AUTO_PLAN_EXECUTE",
    level=5,
    description="Plan & Execute: Turn goals into concrete plans and execute them with tracking.",
    execution="assisted",
    agents=["strategist", "ceo", "documentor"],
    tags=["workflow", "planning", "execution"],
    governance_level="HIGH",
)

AUTO_CHECKLIST = PromptDefinition(
    id="AUTO_CHECKLIST",
    level=3,
    description="Checklist Generator: Create comprehensive checklists for any process or system.",
    execution="assisted",
    agents=["documentor", "validator"],
    tags=["workflow", "checklist", "process"],
    governance_level="LOW",
)

AUTOMATOR = PromptDefinition(
    id="AUTOMATOR",
    level=5,
    description="General Automator: Convert any recurring task into automated pipeline.",
    execution="background",
    agents=["evolver", "validator"],
    tags=["workflow", "automation", "general"],
    governance_level="MEDIUM",
)

AUTO_ORGANIZER = PromptDefinition(
    id="AUTO_ORGANIZER",
    level=4,
    description="Organization Engine: Structure, categorize, and organize information and systems.",
    execution="assisted",
    agents=["organizer", "documentor"],
    tags=["workflow", "organize", "structure"],
    governance_level="LOW",
)


# =============================================================================
# GOVERNANCE & LEGAL DOMAIN PROMPTS
# =============================================================================
AUTO_GOVERNANCE = PromptDefinition(
    id="AUTO_GOVERNANCE",
    level=6,
    description="Governance Engine: Design policies, controls, risk management, access control for systems.",
    execution="assisted",
    agents=["validator", "ceo"],
    tags=["governance", "risk", "compliance"],
    governance_level="CRITICAL",
)

AUTO_LEGAL = PromptDefinition(
    id="AUTO_LEGAL",
    level=5,
    description="Legal Framework: Design legal structures, contracts, policies (not legal advice).",
    execution="assisted",
    agents=["validator", "documentor"],
    tags=["governance", "legal", "contracts"],
    governance_level="CRITICAL",
)

AUTO_SECURITY = PromptDefinition(
    id="AUTO_SECURITY",
    level=6,
    description="Security Engine: Identify vulnerabilities, design security controls, incident response.",
    execution="assisted",
    agents=["validator", "evolver"],
    tags=["governance", "security", "protection"],
    governance_level="CRITICAL",
)

AUTO_HR = PromptDefinition(
    id="AUTO_HR",
    level=4,
    description="HR Engine: People operations, hiring, culture, team dynamics, policies.",
    execution="assisted",
    agents=["strategist", "documentor"],
    tags=["governance", "hr", "people"],
    governance_level="HIGH",
)


# =============================================================================
# SPECIALIZED DOMAIN PROMPTS
# =============================================================================
AUTO_PROBLEM_SOLVER = PromptDefinition(
    id="AUTO_PROBLEM_SOLVER",
    level=5,
    description="Universal Problem Solver: Structured problem analysis, solution generation, validation.",
    execution="assisted",
    agents=["strategist", "validator", "predictor"],
    tags=["special", "problem", "solution"],
    governance_level="MEDIUM",
)

AUTO_STRATEGIST = PromptDefinition(
    id="AUTO_STRATEGIST",
    level=5,
    description="Strategy Engine: Design comprehensive strategies with objectives, metrics, risks.",
    execution="assisted",
    agents=["strategist", "visionary", "ceo"],
    tags=["special", "strategy", "planning"],
    governance_level="HIGH",
)

AUTO_QUANTUM_MIND = PromptDefinition(
    id="AUTO_QUANTUM_MIND",
    level=7,
    description="Quantum-Inspired Reasoning: Superposition of hypotheses, cross-domain synthesis, uncertainty modeling.",
    execution="background",
    agents=["visionary", "predictor", "ceo"],
    tags=["special", "quantum", "reasoning"],
    governance_level="CRITICAL",
)

AUTO_HUMANIZER = PromptDefinition(
    id="AUTO_HUMANIZER",
    level=3,
    description="Humanizer: Make AI outputs more natural, relatable, and human-sounding.",
    execution="assisted",
    agents=["visionary", "documentor"],
    tags=["special", "humanize", "content"],
    governance_level="LOW",
)

AUTO_SUPPORT_SUCCESS = PromptDefinition(
    id="AUTO_SUPPORT_SUCCESS",
    level=4,
    description="Support & Success: Customer support, success management, satisfaction optimization.",
    execution="assisted",
    agents=["documentor", "validator"],
    tags=["special", "support", "success"],
    governance_level="MEDIUM",
)

PROMPT_WRITER = PromptDefinition(
    id="PROMPT_WRITER",
    level=4,
    description="Prompt Engineering: Design, optimize, and validate prompts for AI systems.",
    execution="assisted",
    agents=["documentor", "validator"],
    tags=["special", "prompts", "engineering"],
    governance_level="MEDIUM",
)


# =============================================================================
# DOMAIN REGISTRY
# =============================================================================
DOMAIN_PROMPT_REGISTRY: Dict[str, PromptDefinition] = {
    # System
    "AUTO_ALL": AUTO_ALL,
    "AUTO_BUILD": AUTO_BUILD,
    "AUTO_DIAGNOSE": AUTO_DIAGNOSE,
    "AUTO_FIX": AUTO_FIX,
    "AUTO_HEAL": AUTO_HEAL,
    "AUTO_EVOLVE": AUTO_EVOLVE,
    "AUTO_SYNC": AUTO_SYNC,
    "AUTO_VALIDATE": AUTO_VALIDATE,
    "AUTO_PARALLEL": AUTO_PARALLEL,
    "AUTO_ORCHESTRATOR": AUTO_ORCHESTRATOR,
    "AUTO_MAINTAIN": AUTO_MAINTAIN,
    "AUTO_SANDBOX": AUTO_SANDBOX,
    "AUTO_PRODUCTION": AUTO_PRODUCTION,
    "AUTO_MIRROR": AUTO_MIRROR,
    "AUTO_INDEXER": AUTO_INDEXER,
    "AUTO_INGEST": AUTO_INGEST,
    "AUTO_COMPILE": AUTO_COMPILE,
    "AUTO_GOOGLE": AUTO_GOOGLE,
    # Business
    "AUTO_BRAND": AUTO_BRAND,
    "AUTO_BUDGET": AUTO_BUDGET,
    "AUTO_MARKETING": AUTO_MARKETING,
    "AUTO_MARKET_ANALYSIS": AUTO_MARKET_ANALYSIS,
    "AUTO_COMPETITION": AUTO_COMPETITION,
    "AUTO_MONEY_MAKER": AUTO_MONEY_MAKER,
    "AUTO_MVP": AUTO_MVP,
    "AUTO_NAME": AUTO_NAME,
    "AUTO_NICHE_FINDER": AUTO_NICHE_FINDER,
    "AUTO_VIRAL": AUTO_VIRAL,
    "AUTO_WEBSITE": AUTO_WEBSITE,
    "AUTO_SOCIAL": AUTO_SOCIAL,
    "AUTO_LOGO": AUTO_LOGO,
    "AUTO_OPEN_SOURCE": AUTO_OPEN_SOURCE,
    "AUTO_ENTERPRISE": AUTO_ENTERPRISE,
    # Personal
    "AUTO_PERSONAL": AUTO_PERSONAL,
    "AUTO_PASSION": AUTO_PASSION,
    "AUTO_FREE": AUTO_FREE,
    # Docs
    "AUTO_DOC_CREATE": AUTO_DOC_CREATE,
    "AUTO_DOC_EVOLVE": AUTO_DOC_EVOLVE,
    "AUTO_DOC_TRANSFORM": AUTO_DOC_TRANSFORM,
    # Analysis
    "AUTO_GAP_ANALYZER": AUTO_GAP_ANALYZER,
    "AUTO_CONSENSUS": AUTO_CONSENSUS,
    "AUTO_PREDICTOR": AUTO_PREDICTOR,
    "AUTO_TREND": AUTO_TREND,
    "AUTO_TOP_5": AUTO_TOP_5,
    # Workflow
    "AUTO_WORKFLOW": AUTO_WORKFLOW,
    "AUTO_PLAN_EXECUTE": AUTO_PLAN_EXECUTE,
    "AUTO_CHECKLIST": AUTO_CHECKLIST,
    "AUTOMATOR": AUTOMATOR,
    "AUTO_ORGANIZER": AUTO_ORGANIZER,
    # Governance
    "AUTO_GOVERNANCE": AUTO_GOVERNANCE,
    "AUTO_LEGAL": AUTO_LEGAL,
    "AUTO_SECURITY": AUTO_SECURITY,
    "AUTO_HR": AUTO_HR,
    # Special
    "AUTO_PROBLEM_SOLVER": AUTO_PROBLEM_SOLVER,
    "AUTO_STRATEGIST": AUTO_STRATEGIST,
    "AUTO_QUANTUM_MIND": AUTO_QUANTUM_MIND,
    "AUTO_HUMANIZER": AUTO_HUMANIZER,
    "AUTO_SUPPORT_SUCCESS": AUTO_SUPPORT_SUCCESS,
    "PROMPT_WRITER": PROMPT_WRITER,
}

# Domain short aliases (lowercase → canonical ID)
DOMAIN_ALIASES: Dict[str, str] = {
    # System
    "all": "AUTO_ALL",
    "build": "AUTO_BUILD",
    "diagnose": "AUTO_DIAGNOSE",
    "fix": "AUTO_FIX",
    "heal": "AUTO_HEAL",
    "evolve": "AUTO_EVOLVE",
    "sync": "AUTO_SYNC",
    "validate": "AUTO_VALIDATE",
    "parall": "AUTO_PARALLEL",
    "orchestrate": "AUTO_ORCHESTRATOR",
    "maintain": "AUTO_MAINTAIN",
    "sandbox": "AUTO_SANDBOX",
    "production": "AUTO_PRODUCTION",
    "mirror": "AUTO_MIRROR",
    "index": "AUTO_INDEXER",
    "ingest2": "AUTO_INGEST",
    "compile": "AUTO_COMPILE",
    "google": "AUTO_GOOGLE",
    # Business
    "brand": "AUTO_BRAND",
    "budget": "AUTO_BUDGET",
    "marketing": "AUTO_MARKETING",
    "marketanalysis": "AUTO_MARKET_ANALYSIS",
    "competition": "AUTO_COMPETITION",
    "moneymaker": "AUTO_MONEY_MAKER",
    "revenue": "AUTO_MONEY_MAKER",
    "mvp": "AUTO_MVP",
    "name": "AUTO_NAME",
    "niche": "AUTO_NICHE_FINDER",
    "viral": "AUTO_VIRAL",
    "website": "AUTO_WEBSITE",
    "social": "AUTO_SOCIAL",
    "logo": "AUTO_LOGO",
    "oss": "AUTO_OPEN_SOURCE",
    "enterprise": "AUTO_ENTERPRISE",
    # Personal
    "personal": "AUTO_PERSONAL",
    "passion": "AUTO_PASSION",
    "free": "AUTO_FREE",
    # Docs
    "docs": "AUTO_DOC_CREATE",
    "docsevolve": "AUTO_DOC_EVOLVE",
    "docstransform": "AUTO_DOC_TRANSFORM",
    # Analysis
    "gap": "AUTO_GAP_ANALYZER",
    "consensus": "AUTO_CONSENSUS",
    "predictor": "AUTO_PREDICTOR",
    "trend": "AUTO_TREND",
    "top5": "AUTO_TOP_5",
    # Workflow
    "workflow": "AUTO_WORKFLOW",
    "planexec": "AUTO_PLAN_EXECUTE",
    "checklist": "AUTO_CHECKLIST",
    "automate": "AUTOMATOR",
    "organize": "AUTO_ORGANIZER",
    # Governance
    "governance": "AUTO_GOVERNANCE",
    "legal": "AUTO_LEGAL",
    "security": "AUTO_SECURITY",
    "hr": "AUTO_HR",
    # Special
    "solver": "AUTO_PROBLEM_SOLVER",
    "strategist": "AUTO_STRATEGIST",
    "quantum": "AUTO_QUANTUM_MIND",
    "humanize": "AUTO_HUMANIZER",
    "support": "AUTO_SUPPORT_SUCCESS",
    "promptwrite": "PROMPT_WRITER",
}


def resolve_domain_alias(name: str) -> Optional[PromptDefinition]:
    """Resolve domain alias or direct ID to PromptDefinition."""
    canonical = DOMAIN_ALIASES.get(name.lower(), name.upper())
    return DOMAIN_PROMPT_REGISTRY.get(canonical)


def list_domain_prompts(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    level: Optional[int] = None,
) -> List[PromptDefinition]:
    """List domain prompts, optionally filtering by category/tag/level."""
    results = list(DOMAIN_PROMPT_REGISTRY.values())
    if category:
        results = [
            p for p in results if category.lower() in (t.lower() for t in p.tags)
        ]
    if tag:
        results = [p for p in results if tag.lower() in (t.lower() for t in p.tags)]
    if level is not None:
        results = [p for p in results if p.level == level]
    return results


def get_domain_categories() -> List[str]:
    """Get unique top-level categories from domain prompts."""
    categories = set()
    for prompt in DOMAIN_PROMPT_REGISTRY.values():
        if prompt.tags:
            categories.add(prompt.tags[0])
    return sorted(categories)
