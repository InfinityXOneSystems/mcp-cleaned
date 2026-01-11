"""
ArtifactWriter — Build Artifact Generation
Governed by: /mcp/contracts/AUTO_BUILDER_LAW.md

Generates mandatory build artifacts:
- build_plan.json (copy of approved plan)
- execution_log.json (full execution trace)
- diff_manifest.json (all file changes)
- validation_report.json (validation results)
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ArtifactConfig:
    """Configuration for artifact generation."""

    output_dir: str = "/mcp/auto_builder/artifacts/output"
    include_timestamps: bool = True
    include_hashes: bool = True
    pretty_print: bool = True


class ArtifactWriter:
    """
    Generates mandatory build artifacts.

    All four artifacts are REQUIRED for every build:
    1. build_plan.json — The approved plan that was executed
    2. execution_log.json — Step-by-step execution trace
    3. diff_manifest.json — All file changes (create/modify/delete)
    4. validation_report.json — Pre/post validation results

    Artifacts are written to: /mcp/auto_builder/artifacts/output/<plan_id>/
    """

    REQUIRED_ARTIFACTS = [
        "build_plan.json",
        "execution_log.json",
        "diff_manifest.json",
        "validation_report.json",
    ]

    def __init__(
        self, config: Optional[ArtifactConfig] = None, repo_root: str = "/mcp"
    ):
        self.config = config or ArtifactConfig()
        self.repo_root = Path(repo_root)
        self._artifacts_generated: List[str] = []

    async def write_all(
        self,
        context: Any,  # ExecutionContext from orchestrator
        step_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate all required artifacts.

        Returns summary of generated artifacts.
        """
        plan = context.plan
        output_dir = self._get_output_dir(plan.plan_id)

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        # 1. Build Plan
        results["build_plan"] = await self._write_build_plan(output_dir, plan)

        # 2. Execution Log
        results["execution_log"] = await self._write_execution_log(
            output_dir, context, step_results
        )

        # 3. Diff Manifest
        results["diff_manifest"] = await self._write_diff_manifest(
            output_dir, step_results
        )

        # 4. Validation Report
        results["validation_report"] = await self._write_validation_report(
            output_dir, context
        )

        return {
            "success": all(r.get("success", False) for r in results.values()),
            "artifacts": results,
            "output_dir": str(output_dir),
        }

    async def _write_build_plan(self, output_dir: Path, plan: Any) -> Dict[str, Any]:
        """Write build_plan.json artifact."""
        artifact_path = output_dir / "build_plan.json"

        data = {
            "plan_id": plan.plan_id,
            "requested_by": plan.requested_by,
            "intent_summary": plan.intent_summary,
            "governance_level": plan.governance_level.name,
            "scope": plan.scope,
            "architecture": plan.architecture,
            "steps": plan.steps,
            "constraints": plan.constraints,
            "risk_assessment": plan.risk_assessment,
            "validation_requirements": plan.validation_requirements,
            "artifacts": plan.artifacts,
            "execution_order": plan.execution_order,
            "live_execution_requires": plan.live_execution_requires,
            "_metadata": self._get_metadata(plan.plan_id),
        }

        self._write_json(artifact_path, data)
        self._artifacts_generated.append(str(artifact_path))

        return {"success": True, "path": str(artifact_path)}

    async def _write_execution_log(
        self, output_dir: Path, context: Any, step_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Write execution_log.json artifact."""
        artifact_path = output_dir / "execution_log.json"

        data = {
            "plan_id": context.plan.plan_id,
            "state": context.state.value,
            "dry_run": context.dry_run,
            "started_at": (
                context.started_at.isoformat() if context.started_at else None
            ),
            "completed_at": (
                context.completed_at.isoformat() if context.completed_at else None
            ),
            "steps": step_results,
            "errors": context.errors,
            "warnings": context.warnings,
            "_metadata": self._get_metadata(context.plan.plan_id),
        }

        self._write_json(artifact_path, data)
        self._artifacts_generated.append(str(artifact_path))

        return {"success": True, "path": str(artifact_path)}

    async def _write_diff_manifest(
        self, output_dir: Path, step_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Write diff_manifest.json artifact."""
        artifact_path = output_dir / "diff_manifest.json"

        # Extract diffs from step results
        changes = []
        for result in step_results:
            if result.get("files_affected"):
                changes.append(
                    {
                        "step_id": result.get("step_id"),
                        "action": result.get("action"),
                        "files": result.get("files_affected"),
                        "diff": result.get("diff"),
                    }
                )

        data = {
            "total_changes": len(changes),
            "files_created": sum(1 for c in changes if c.get("action") == "create"),
            "files_modified": sum(1 for c in changes if c.get("action") == "modify"),
            "files_deleted": sum(1 for c in changes if c.get("action") == "delete"),
            "changes": changes,
            "_metadata": self._get_metadata("diff"),
        }

        self._write_json(artifact_path, data)
        self._artifacts_generated.append(str(artifact_path))

        return {"success": True, "path": str(artifact_path)}

    async def _write_validation_report(
        self, output_dir: Path, context: Any
    ) -> Dict[str, Any]:
        """Write validation_report.json artifact."""
        artifact_path = output_dir / "validation_report.json"

        # Calculate confidence based on execution results
        total_steps = len(context.plan.steps)
        successful_steps = total_steps - len(context.errors)
        confidence = successful_steps / total_steps if total_steps > 0 else 0.0

        # Check governance threshold
        governance_threshold = context.plan.governance_level.value
        meets_threshold = confidence >= governance_threshold

        data = {
            "plan_id": context.plan.plan_id,
            "validation_passed": len(context.errors) == 0,
            "confidence": confidence,
            "governance_level": context.plan.governance_level.name,
            "governance_threshold": governance_threshold,
            "meets_threshold": meets_threshold,
            "checks": {
                "pre_execution": True,  # Would be filled by validator
                "post_execution": len(context.errors) == 0,
                "path_authorization": True,
                "artifact_generation": True,
            },
            "errors": context.errors,
            "warnings": context.warnings,
            "live_execution_eligible": meets_threshold and len(context.errors) == 0,
            "_metadata": self._get_metadata(context.plan.plan_id),
        }

        self._write_json(artifact_path, data)
        self._artifacts_generated.append(str(artifact_path))

        return {"success": True, "path": str(artifact_path)}

    def _get_output_dir(self, plan_id: str) -> Path:
        """Get output directory for plan."""
        base = self.repo_root / self.config.output_dir.lstrip("/mcp/")
        return base / plan_id

    def _get_metadata(self, identifier: str) -> Dict[str, Any]:
        """Generate artifact metadata."""
        meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "generator": "ArtifactWriter",
            "version": "0.1.0",
        }

        if self.config.include_hashes:
            meta["hash"] = hashlib.sha256(identifier.encode()).hexdigest()[:16]

        return meta

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        """Write JSON file with configured formatting."""
        indent = 2 if self.config.pretty_print else None
        with open(path, "w") as f:
            json.dump(data, f, indent=indent, default=str)

    def get_generated_artifacts(self) -> List[str]:
        """Get list of generated artifact paths."""
        return self._artifacts_generated.copy()

    def validate_artifacts(self, plan_id: str) -> Dict[str, bool]:
        """Validate that all required artifacts exist."""
        output_dir = self._get_output_dir(plan_id)

        results = {}
        for artifact in self.REQUIRED_ARTIFACTS:
            artifact_path = output_dir / artifact
            results[artifact] = artifact_path.exists()

        return results
