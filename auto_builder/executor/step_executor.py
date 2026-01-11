"""
StepExecutor — Individual Build Step Execution
Governed by: /mcp/contracts/AUTO_BUILDER_LAW.md

Executes individual build steps with validation gates.
Respects dry_run mode — no file system changes in dry run.
"""

import difflib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class StepAction(Enum):
    """Canonical step actions."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class StepStatus(Enum):
    """Step execution status."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of step execution."""

    step_id: str
    action: StepAction
    status: StepStatus
    files_affected: List[str] = field(default_factory=list)
    diff: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    dry_run: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action.value,
            "status": self.status.value,
            "files_affected": self.files_affected,
            "diff": self.diff,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "dry_run": self.dry_run,
        }


class StepExecutor:
    """
    Executes individual build steps.

    Responsibilities:
    1. Parse step definition
    2. Validate preconditions
    3. Execute action (or simulate in dry_run)
    4. Generate diff
    5. Return result

    CRITICAL: In dry_run mode, NO file system changes.
    """

    # Authorized write paths (mirrors orchestrator)
    AUTHORIZED_PATHS = [
        "/mcp/vision_cortex/",
        "/mcp/auto_builder/",
        "/mcp/validator/",
        "/mcp/contracts/",
        "/mcp/index/",
        "/mcp/dev_evolution/",
    ]

    def __init__(self, repo_root: str = "/mcp"):
        self.repo_root = Path(repo_root)
        self._pending_changes: List[Dict[str, Any]] = []

    async def execute_step(
        self,
        step: Dict[str, Any],
        context: Any,  # ExecutionContext from orchestrator
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a single build step.

        Step schema:
        {
            "step_id": "S01",
            "description": "Create folder structure",
            "action": "create",
            "files": ["/mcp/vision_cortex/new_file.py"],
            "content": "...",  # For create/modify
            "dependencies": ["S00"],  # Optional
            "validation_gate": "G01"  # Optional
        }
        """
        step_id = step.get("step_id", "UNKNOWN")
        action_str = step.get("action", "create")
        files = step.get("files", [])

        try:
            action = StepAction(action_str)
        except ValueError:
            return StepResult(
                step_id=step_id,
                action=StepAction.CREATE,
                status=StepStatus.FAILED,
                error=f"Invalid action: {action_str}",
            ).to_dict()

        # Validate paths
        for file_path in files:
            if not self._is_authorized_path(file_path):
                return StepResult(
                    step_id=step_id,
                    action=action,
                    status=StepStatus.FAILED,
                    error=f"Unauthorized path: {file_path}",
                ).to_dict()

        # Execute based on action
        if action == StepAction.CREATE:
            result = await self._execute_create(step, dry_run)
        elif action == StepAction.MODIFY:
            result = await self._execute_modify(step, dry_run)
        elif action == StepAction.DELETE:
            result = await self._execute_delete(step, dry_run)
        else:
            result = StepResult(
                step_id=step_id,
                action=action,
                status=StepStatus.FAILED,
                error=f"Unsupported action: {action_str}",
            )

        result.dry_run = dry_run
        return result.to_dict()

    async def _execute_create(self, step: Dict[str, Any], dry_run: bool) -> StepResult:
        """Execute create action."""
        step_id = step.get("step_id", "UNKNOWN")
        files = step.get("files", [])
        content = step.get("content", "")

        affected = []
        diffs = []

        for file_path in files:
            full_path = self._resolve_path(file_path)

            if dry_run:
                # Simulate creation
                self._pending_changes.append(
                    {"action": "create", "path": file_path, "content": content}
                )
                diffs.append(f"+++ {file_path} (NEW FILE)\n{content[:500]}...")
            else:
                # Actual creation
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content)

            affected.append(file_path)

        return StepResult(
            step_id=step_id,
            action=StepAction.CREATE,
            status=StepStatus.COMPLETED,
            files_affected=affected,
            diff="\n".join(diffs) if diffs else None,
        )

    async def _execute_modify(self, step: Dict[str, Any], dry_run: bool) -> StepResult:
        """Execute modify action."""
        step_id = step.get("step_id", "UNKNOWN")
        files = step.get("files", [])
        content = step.get("content", "")

        affected = []
        diffs = []

        for file_path in files:
            full_path = self._resolve_path(file_path)

            # Read existing content
            old_content = ""
            if full_path.exists():
                with open(full_path, "r") as f:
                    old_content = f.read()

            # Generate diff
            diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
            diff_str = "".join(diff)
            diffs.append(diff_str)

            if dry_run:
                self._pending_changes.append(
                    {
                        "action": "modify",
                        "path": file_path,
                        "old_content": old_content,
                        "new_content": content,
                    }
                )
            else:
                with open(full_path, "w") as f:
                    f.write(content)

            affected.append(file_path)

        return StepResult(
            step_id=step_id,
            action=StepAction.MODIFY,
            status=StepStatus.COMPLETED,
            files_affected=affected,
            diff="\n".join(diffs) if diffs else None,
        )

    async def _execute_delete(self, step: Dict[str, Any], dry_run: bool) -> StepResult:
        """Execute delete action."""
        step_id = step.get("step_id", "UNKNOWN")
        files = step.get("files", [])

        affected = []
        diffs = []

        for file_path in files:
            full_path = self._resolve_path(file_path)

            if dry_run:
                if full_path.exists():
                    with open(full_path, "r") as f:
                        old_content = f.read()
                    diffs.append(f"--- {file_path} (DELETED)\n{old_content[:500]}...")
                    self._pending_changes.append(
                        {
                            "action": "delete",
                            "path": file_path,
                            "old_content": old_content,
                        }
                    )
            else:
                if full_path.exists():
                    full_path.unlink()

            affected.append(file_path)

        return StepResult(
            step_id=step_id,
            action=StepAction.DELETE,
            status=StepStatus.COMPLETED,
            files_affected=affected,
            diff="\n".join(diffs) if diffs else None,
        )

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path to absolute path."""
        if file_path.startswith("/mcp/"):
            return self.repo_root / file_path[5:]
        return self.repo_root / file_path

    def _is_authorized_path(self, path: str) -> bool:
        """Check if path is authorized for writes."""
        for auth_path in self.AUTHORIZED_PATHS:
            if path.startswith(auth_path):
                return True
        return False

    def get_pending_changes(self) -> List[Dict[str, Any]]:
        """Get list of pending changes (from dry run)."""
        return self._pending_changes.copy()

    def clear_pending(self) -> None:
        """Clear pending changes."""
        self._pending_changes = []
