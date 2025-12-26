"""
ValidatorGate — Pre/Post Execution Validation with Kill Switch
Governed by: /mcp/contracts/AUTO_BUILDER_LAW.md

Validator has kill switch authority.
Can abort any build at any time.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime


class ValidationResult(Enum):
    """Validation outcome."""
    APPROVED = "approved"
    REJECTED = "rejected"
    WARNING = "warning"
    KILL_SWITCH = "kill_switch"


@dataclass
class ValidationCheck:
    """Individual validation check."""
    name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ValidationReport:
    """Complete validation report."""
    result: ValidationResult
    checks: List[ValidationCheck]
    confidence: float
    approved: bool
    kill_switch_triggered: bool = False
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result.value,
            "checks": [c.to_dict() for c in self.checks],
            "confidence": self.confidence,
            "approved": self.approved,
            "kill_switch_triggered": self.kill_switch_triggered,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat()
        }


class ValidatorGate:
    """
    Validation gate with kill switch authority.
    
    Authority:
    - Can REJECT any build plan
    - Can ABORT execution at any step
    - Can trigger KILL SWITCH for immediate halt
    
    Pre-Execution Checks:
    - Plan schema validation
    - Path authorization
    - Governance level compliance
    - Constraint satisfaction
    
    Post-Execution Checks:
    - All steps completed
    - No unauthorized changes
    - Artifacts generated
    - Confidence threshold met
    """
    
    # Kill switch triggers (immediate abort)
    KILL_SWITCH_TRIGGERS = [
        "unauthorized_path_access",
        "governance_violation",
        "security_breach",
        "memory_corruption",
        "agent_collapse"
    ]
    
    # Authorized paths (must match orchestrator)
    AUTHORIZED_PATHS = [
        "/mcp/vision_cortex/",
        "/mcp/auto_builder/",
        "/mcp/validator/",
        "/mcp/contracts/",
        "/mcp/index/",
        "/mcp/dev_evolution/"
    ]
    
    def __init__(self):
        self._kill_switch_active = False
        self._kill_switch_reason: Optional[str] = None
        self._validation_history: List[ValidationReport] = []
    
    # ─────────────────────────────────────────────────────────────────────
    # PRE-EXECUTION VALIDATION
    # ─────────────────────────────────────────────────────────────────────
    
    async def pre_execution_check(self, context: Any) -> Dict[str, Any]:
        """
        Pre-execution validation gate.
        
        Must pass before any build step executes.
        """
        checks = []
        plan = context.plan
        
        # Check 1: Plan ID present
        checks.append(ValidationCheck(
            name="plan_id_present",
            passed=bool(plan.plan_id),
            message="Plan ID is required"
        ))
        
        # Check 2: Valid requester
        checks.append(ValidationCheck(
            name="valid_requester",
            passed=plan.requested_by == "VisionCortex",
            message=f"Requester must be VisionCortex, got {plan.requested_by}"
        ))
        
        # Check 3: Authorized paths
        path_violations = []
        for path in plan.scope.get("write_paths", []):
            if not self._is_authorized_path(path):
                path_violations.append(path)
        
        checks.append(ValidationCheck(
            name="authorized_paths",
            passed=len(path_violations) == 0,
            message=f"Unauthorized paths: {path_violations}" if path_violations else "All paths authorized"
        ))
        
        # Check 4: Has steps
        checks.append(ValidationCheck(
            name="has_steps",
            passed=len(plan.steps) > 0,
            message="Build plan must have at least one step"
        ))
        
        # Check 5: Required artifacts declared
        required = ["build_plan.json", "execution_log.json", "diff_manifest.json", "validation_report.json"]
        missing = [a for a in required if a not in plan.artifacts]
        checks.append(ValidationCheck(
            name="required_artifacts",
            passed=len(missing) == 0,
            message=f"Missing artifacts: {missing}" if missing else "All artifacts declared"
        ))
        
        # Check 6: Governance level valid
        checks.append(ValidationCheck(
            name="governance_level",
            passed=plan.governance_level is not None,
            message="Governance level must be specified"
        ))
        
        # Check for kill switch triggers
        if len(path_violations) > 0:
            self._trigger_kill_switch("unauthorized_path_access")
        
        # Calculate confidence
        passed = sum(1 for c in checks if c.passed)
        confidence = passed / len(checks) if checks else 0.0
        
        # Determine result
        all_passed = all(c.passed for c in checks)
        
        report = ValidationReport(
            result=ValidationResult.APPROVED if all_passed else ValidationResult.REJECTED,
            checks=checks,
            confidence=confidence,
            approved=all_passed and not self._kill_switch_active,
            kill_switch_triggered=self._kill_switch_active,
            reason=self._kill_switch_reason
        )
        
        self._validation_history.append(report)
        
        return report.to_dict()
    
    # ─────────────────────────────────────────────────────────────────────
    # POST-EXECUTION VALIDATION
    # ─────────────────────────────────────────────────────────────────────
    
    async def post_execution_check(
        self,
        context: Any,
        step_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Post-execution validation gate.
        
        Must pass before build is considered complete.
        """
        checks = []
        plan = context.plan
        
        # Check 1: All steps completed
        completed = sum(1 for r in step_results if r.get("status") == "completed")
        checks.append(ValidationCheck(
            name="steps_completed",
            passed=completed == len(plan.steps),
            message=f"{completed}/{len(plan.steps)} steps completed"
        ))
        
        # Check 2: No failures
        failures = [r for r in step_results if r.get("status") == "failed"]
        checks.append(ValidationCheck(
            name="no_failures",
            passed=len(failures) == 0,
            message=f"{len(failures)} steps failed" if failures else "No failures"
        ))
        
        # Check 3: No errors in context
        checks.append(ValidationCheck(
            name="no_context_errors",
            passed=len(context.errors) == 0,
            message=f"{len(context.errors)} errors" if context.errors else "No errors"
        ))
        
        # Check 4: Path authorization (verify all changes were authorized)
        unauthorized = []
        for result in step_results:
            for path in result.get("files_affected", []):
                if not self._is_authorized_path(path):
                    unauthorized.append(path)
        
        checks.append(ValidationCheck(
            name="all_changes_authorized",
            passed=len(unauthorized) == 0,
            message=f"Unauthorized changes: {unauthorized}" if unauthorized else "All changes authorized"
        ))
        
        # Check 5: Confidence meets governance threshold
        governance_threshold = plan.governance_level.value
        actual_confidence = (completed / len(plan.steps)) if plan.steps else 0.0
        checks.append(ValidationCheck(
            name="confidence_threshold",
            passed=actual_confidence >= governance_threshold,
            message=f"Confidence {actual_confidence:.2f} vs threshold {governance_threshold:.2f}"
        ))
        
        # Calculate confidence
        passed = sum(1 for c in checks if c.passed)
        confidence = passed / len(checks) if checks else 0.0
        
        # Determine result
        all_passed = all(c.passed for c in checks)
        
        report = ValidationReport(
            result=ValidationResult.APPROVED if all_passed else ValidationResult.REJECTED,
            checks=checks,
            confidence=confidence,
            approved=all_passed and not self._kill_switch_active,
            kill_switch_triggered=self._kill_switch_active,
            reason=self._kill_switch_reason
        )
        
        self._validation_history.append(report)
        
        return report.to_dict()
    
    # ─────────────────────────────────────────────────────────────────────
    # KILL SWITCH
    # ─────────────────────────────────────────────────────────────────────
    
    def _trigger_kill_switch(self, reason: str) -> None:
        """Trigger kill switch — immediate halt of all operations."""
        self._kill_switch_active = True
        self._kill_switch_reason = reason
    
    def trigger_kill_switch(self, reason: str) -> Dict[str, Any]:
        """Public method to trigger kill switch."""
        self._trigger_kill_switch(reason)
        return {
            "kill_switch_active": True,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_kill_switch(self, authorization_code: str) -> bool:
        """
        Reset kill switch (requires authorization).
        
        Only VisionCortex CEO agent or human operator can reset.
        """
        # In production, this would verify the authorization code
        if authorization_code == "VISION_CORTEX_CEO_OVERRIDE":
            self._kill_switch_active = False
            self._kill_switch_reason = None
            return True
        return False
    
    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is active."""
        return self._kill_switch_active
    
    # ─────────────────────────────────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────────────────────────────────
    
    def _is_authorized_path(self, path: str) -> bool:
        """Check if path is authorized."""
        for auth_path in self.AUTHORIZED_PATHS:
            if path.startswith(auth_path):
                return True
        return False
    
    def get_validation_history(self) -> List[Dict[str, Any]]:
        """Get validation history for audit."""
        return [r.to_dict() for r in self._validation_history]
    
    def get_status(self) -> Dict[str, Any]:
        """Get validator status."""
        return {
            "kill_switch_active": self._kill_switch_active,
            "kill_switch_reason": self._kill_switch_reason,
            "validations_performed": len(self._validation_history),
            "last_validation": self._validation_history[-1].to_dict() if self._validation_history else None
        }
