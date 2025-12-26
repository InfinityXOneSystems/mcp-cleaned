# Vision Cortex — Architecture

## Purpose
A living intelligence layer for Infinity X that performs long-horizon reasoning, prediction, debate, strategy, and invention. Built as a multi-agent, continuously learning system anchored to enterprise governance (SAFE_MODE enforced).

## Core Roles (Multi-AI Civilization)
- Crawler: gather external signals.
- Ingestor: clean, normalize, embed.
- Organizer: structure knowledge and graph relationships.
- Predictor: forecast trends and scenarios.
- Visionary: imagine futures and possibilities.
- Strategist: backcast plans from desired futures.
- CEO: prioritize decisions and allocate attention.
- Validator: critique, stress-test, enforce policy.
- Documentor: produce human-readable outputs.
- Evolver: propose improvements, tune prompts/routing, and retire/spawn agents.

## Communication Fabric
- Pub/Sub topics over a unified message bus (in-repo stub; pluggable for GCP Pub/Sub).
- Smart Router: intent → agent mapping; route by role, priority, and governance level.
- Omni Gateway + MCP layer for external requests; agents never act in isolation.
- Middleware on bus for correlation and audit; subscriber failures are isolated.

## Unified Brain & Memory
- Long-term memory: Firestore collection `mcp_memory`.
- Semantic memory: embeddings store (pluggable, vector backend TBD).
- Episodic memory: agent conversation/event logs.
- Working memory: per-task context passed via message payloads.
- Every interaction: logged, timestamped, attributed, persisted for learning.
- In-memory fallback for local/dev; Firestore preferred when available.

## Continuous Loop (Infinity Feedback Loop)
monitor → analyze → debate → decide → execute → validate → persist → evolve
- Scheduled + event-driven.
- Tracks confidence, contradictions, and blind spots.
- Improves prompts, heuristics, routing, and structures.

## Quantum-Inspired Reasoning Tags
Use explicit tags to disambiguate certainty:
- [REAL-TODAY] observed facts and validated data
- [EMERGING] early signals with partial evidence
- [HYPOTHETICAL] imaginative futures and designs
- [UNCERTAIN] unclear or conflicting evidence

## Safety & Governance
- Governance tiers: LOW/ MEDIUM/ HIGH/ CRITICAL (default UP if unclear).
- SAFE_MODE always on; CRITICAL requires explicit human confirmation.
- All actions: log intent, result, follow-up checks; keep dissent when valuable.

## Observability
- Logs per agent with topic, correlation IDs, confidence.
- Metrics: task latency, success rate, debate depth, consensus vs dissent.
- Memory traces stored to Firestore and vector store for recall.
- Tests cover bus, ingestion, and debate flows; debate cycle records consensus vs dissent.

## Directories
- agents/: role implementations and base class.
- comms/: message bus and router stubs.
- memory/: registry for Firestore + embeddings.
- pipelines/: ingestion and continuous loop orchestrators.
- validators/: policy, safety, and hallucination checks.
- ui/: operator surfaces (status, debates, confidence, dissent).
- tests/: safety harness and regression checks.
- schemas/: shared contracts for messages, debate turns, plans, and predictions.

## Integration Points
- Gateway: https://gateway.infinityxoneintelligence.com (X-MCP-KEY auth).
- Firestore: `mcp_memory` (project `infinity-x-one-systems`).
- Agents run under SAFE_MODE and must log to memory via registry hooks.

## Evolution Protocol
- After each major cycle: review what was learned, what broke, what to automate next.
- Add/retire agents based on performance; update prompts and routing heuristics.
- Preserve dissenting views; promote durable patterns to templates.
