"""
BuildOrchestrator — Governed Construction Engine
Governed by: /mcp/contracts/AUTO_BUILDER_LAW.md

Coordinates build execution according to approved plans.
NO CODE GENERATION without approved build_plan.json.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class BuildState(Enum):
    """Canonical build states."""

    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class GovernanceLevel(Enum):
    """Governance levels with confidence thresholds."""

    LOW = 0.5
    MEDIUM = 0.7
    HIGH = 0.85
    CRITICAL = 0.95


@dataclass
class BuildPlan:
    """
    Validated build plan structure.
    Must conform to /mcp/contracts/BUILD_PLAN.schema.json
    """

    plan_id: str
    requested_by: str
    intent_summary: str
    governance_level: GovernanceLevel
    scope: Dict[str, List[str]]
    architecture: Dict[str, Any]
    steps: List[Dict[str, Any]]
    constraints: List[str]
    risk_assessment: str
    validation_requirements: List[str]
    artifacts: List[str]

    # Normalized execution order (machine-addressable)
    execution_order: List[str] = field(default_factory=list)

    # Live execution requirements
    live_execution_requires: List[str] = field(
        default_factory=lambda: [
            "validation_report.confidence >= governance_threshold",
            "validator.approval == true",
        ]
    )

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "BuildPlan":
        """Create BuildPlan from JSON data."""
        return cls(
            plan_id=data["plan_id"],
            requested_by=data["requested_by"],
            intent_summary=data["intent_summary"],
            governance_level=GovernanceLevel[data["governance_level"]],
            scope=data["scope"],
            architecture=data["architecture"],
            steps=data["steps"],
            constraints=data["constraints"],
            risk_assessment=data["risk_assessment"],
            validation_requirements=data["validation_requirements"],
            artifacts=data["artifacts"],
            execution_order=data.get("execution_order", []),
            live_execution_requires=data.get(
                "live_execution_requires",
                [
                    "validation_report.confidence >= governance_threshold",
                    "validator.approval == true",
                ],
            ),
        )

    @property
    def plan_hash(self) -> str:
        """Generate deterministic hash of plan for audit."""
        key = f"{self.plan_id}:{self.intent_summary}:{len(self.steps)}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]


@dataclass
class ExecutionContext:
    """Context for build execution."""

    plan: BuildPlan
    state: BuildState = BuildState.PENDING
    current_step: int = 0
    dry_run: bool = True  # MANDATORY DEFAULT
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BuildOrchestrator:
    """
    Master orchestrator for governed build execution.

    Authority Chain:
    1. VisionCortex (requests builds)
    2. BuildOrchestrator (executes plans)
    3. Validator (approves/rejects)

    Mandatory Sequence:
    1. Load build plan
    2. Validate against schema
    3. Check authorized paths
    4. Pre-execution validation gate
    5. Execute steps (dry_run first)
    6. Post-execution validation gate
    7. Generate artifacts
    8. Commit (if approved)
    """

    # Authorized write paths (from contracts)
    AUTHORIZED_PATHS = [
        "/mcp/vision_cortex/",
        "/mcp/auto_builder/",
        "/mcp/validator/",
        "/mcp/contracts/",
        "/mcp/index/",
        "/mcp/dev_evolution/",
    ]

    # Forbidden paths (everything else)
    FORBIDDEN_PATTERNS = [
        "/mcp/omni_gateway.py",
        "/mcp/api_gateway.py",
        "/mcp/.git/",
        "/mcp/node_modules/",
    ]

    def __init__(self, repo_root: str = "/mcp"):
        self.repo_root = Path(repo_root)
        self.context: Optional[ExecutionContext] = None
        self.step_executor = None  # Set by wire_executor()
        self.artifact_writer = None  # Set by wire_artifacts()
        self.validator_gate = None  # Set by wire_validator()
        self._execution_log: List[Dict[str, Any]] = []

    # ─────────────────────────────────────────────────────────────────────
    # PLAN LOADING & VALIDATION
    # ─────────────────────────────────────────────────────────────────────

    def load_plan(self, plan_path: str) -> BuildPlan:
        """Load and validate build plan from JSON file."""
        path = Path(plan_path)
        if not path.exists():
            raise FileNotFoundError(f"Build plan not found: {plan_path}")

        with open(path, "r") as f:
            data = json.load(f)

        plan = BuildPlan.from_json(data)

        # Validate required fields
        violations = self._validate_plan(plan)
        if violations:
            raise ValueError(f"Invalid build plan: {violations}")

        self.context = ExecutionContext(plan=plan)
        self._log("plan_loaded", {"plan_id": plan.plan_id, "hash": plan.plan_hash})

        return plan

    def _validate_plan(self, plan: BuildPlan) -> List[str]:
        """Validate build plan against contracts."""
        violations = []

        # Check requested_by
        if plan.requested_by != "VisionCortex":
            violations.append(
                f"Invalid requester: {plan.requested_by} (must be VisionCortex)"
            )

        # Check paths
        for path in plan.scope.get("write_paths", []):
            if not self._is_authorized_path(path):
                violations.append(f"Unauthorized write path: {path}")

        # Check artifacts
        required_artifacts = [
            "build_plan.json",
            "execution_log.json",
            "diff_manifest.json",
            "validation_report.json",
        ]
        for artifact in required_artifacts:
            if artifact not in plan.artifacts:
                violations.append(f"Missing required artifact: {artifact}")

        # Check steps
        if not plan.steps:
            violations.append("Build plan has no steps")

        return violations

    def _is_authorized_path(self, path: str) -> bool:
        """Check if path is in authorized list."""
        # Check forbidden patterns first
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in path:
                return False

        # Check authorized paths
        for auth_path in self.AUTHORIZED_PATHS:
            if path.startswith(auth_path):
                return True

        return False

    # ─────────────────────────────────────────────────────────────────────
    # EXECUTION CONTROL
    # ─────────────────────────────────────────────────────────────────────

    async def execute(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Execute the loaded build plan.

        MANDATORY: dry_run=True by default.
        Live execution requires:
        - validation_report.confidence >= governance_threshold
        - validator.approval == true
        """
        if self.context is None:
            raise RuntimeError("No build plan loaded")

        self.context.dry_run = dry_run
        self.context.state = BuildState.VALIDATING
        self.context.started_at = datetime.utcnow()

        # Pre-execution validation gate
        if self.validator_gate:
            pre_result = await self.validator_gate.pre_execution_check(self.context)
            if not pre_result["approved"]:
                self.context.state = BuildState.ABORTED
                self._log("pre_validation_failed", pre_result)
                return {
                    "success": False,
                    "reason": "Pre-execution validation failed",
                    **pre_result,
                }

        self.context.state = BuildState.APPROVED
        self._log("execution_started", {"dry_run": dry_run})

        # Execute steps
        self.context.state = BuildState.EXECUTING
        results = []

        for i, step in enumerate(self.context.plan.steps):
            self.context.current_step = i

            try:
                if self.step_executor:
                    result = await self.step_executor.execute_step(
                        step=step, context=self.context, dry_run=dry_run
                    )
                else:
                    result = {
                        "step_id": step.get("step_id"),
                        "status": "skipped",
                        "reason": "No executor",
                    }

                results.append(result)
                self._log("step_completed", result)

                if result.get("status") == "failed":
                    self.context.errors.append(f"Step {step.get('step_id')} failed")
                    if not dry_run:
                        break  # Stop on failure in live mode

            except Exception as e:
                error = {"step_id": step.get("step_id"), "error": str(e)}
                results.append(error)
                self.context.errors.append(str(e))
                self._log("step_error", error)
                break

        # Post-execution validation gate
        if self.validator_gate:
            post_result = await self.validator_gate.post_execution_check(
                self.context, results
            )
            if not post_result["approved"]:
                self.context.state = BuildState.FAILED
                self._log("post_validation_failed", post_result)
                return {
                    "success": False,
                    "reason": "Post-execution validation failed",
                    **post_result,
                }

        # Generate artifacts
        if self.artifact_writer:
            await self.artifact_writer.write_all(self.context, results)

        self.context.state = BuildState.COMPLETED
        self.context.completed_at = datetime.utcnow()
        self._log(
            "execution_completed",
            {"steps": len(results), "errors": len(self.context.errors)},
        )

        return {
            "success": len(self.context.errors) == 0,
            "dry_run": dry_run,
            "steps_executed": len(results),
            "errors": self.context.errors,
            "warnings": self.context.warnings,
        }

    def pause(self) -> None:
        """Pause execution (can be resumed)."""
        if self.context and self.context.state == BuildState.EXECUTING:
            self.context.state = BuildState.PAUSED
            self._log("execution_paused", {"step": self.context.current_step})

    def abort(self, reason: str) -> None:
        """Abort execution (cannot be resumed)."""
        if self.context:
            self.context.state = BuildState.ABORTED
            self.context.errors.append(f"Aborted: {reason}")
            self._log("execution_aborted", {"reason": reason})

    # ─────────────────────────────────────────────────────────────────────
    # WIRING
    # ─────────────────────────────────────────────────────────────────────

    def wire_executor(self, executor) -> None:
        """Wire the step executor."""
        self.step_executor = executor

    def wire_artifacts(self, writer) -> None:
        """Wire the artifact writer."""
        self.artifact_writer = writer

    def wire_validator(self, validator) -> None:
        """Wire the validator gate."""
        self.validator_gate = validator

    # ─────────────────────────────────────────────────────────────────────
    # LOGGING & AUDIT
    # ─────────────────────────────────────────────────────────────────────

    def _log(self, event: str, data: Dict[str, Any]) -> None:
        """Log event to execution log."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data,
            "plan_id": self.context.plan.plan_id if self.context else None,
        }
        self._execution_log.append(entry)

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get full execution log for audit."""
        return self._execution_log.copy()

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        if self.context is None:
            return {"state": "idle", "plan_loaded": False}

        return {
            "state": self.context.state.value,
            "plan_loaded": True,
            "plan_id": self.context.plan.plan_id,
            "current_step": self.context.current_step,
            "total_steps": len(self.context.plan.steps),
            "dry_run": self.context.dry_run,
            "errors": len(self.context.errors),
            "warnings": len(self.context.warnings),
        }
