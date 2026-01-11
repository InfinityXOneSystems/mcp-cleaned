"""
Rollback Engine — Safe System State Restoration
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SnapshotType(Enum):
    """Types of system snapshots."""

    FULL = "full"  # Complete system state
    INCREMENTAL = "incremental"  # Changes since last snapshot
    CHECKPOINT = "checkpoint"  # Manual checkpoint


class RollbackStatus(Enum):
    """Status of rollback operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


@dataclass
class SystemSnapshot:
    """
    Point-in-time system state snapshot.

    Captures:
    - Agent configurations
    - Memory state
    - Prompt definitions
    - Weights and thresholds
    """

    snapshot_id: str
    snapshot_type: SnapshotType
    state: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    integrity_hash: str = ""

    def __post_init__(self):
        if not self.snapshot_id:
            key = f"{self.snapshot_type.value}:{self.timestamp.isoformat()}"
            self.snapshot_id = hashlib.sha256(key.encode()).hexdigest()[:16]

        if not self.integrity_hash:
            state_str = json.dumps(self.state, sort_keys=True, default=str)
            self.integrity_hash = hashlib.sha256(state_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify snapshot integrity."""
        state_str = json.dumps(self.state, sort_keys=True, default=str)
        computed_hash = hashlib.sha256(state_str.encode()).hexdigest()
        return computed_hash == self.integrity_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_type": self.snapshot_type.value,
            "state": self.state,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "integrity_hash": self.integrity_hash,
        }


@dataclass
class RollbackOperation:
    """Rollback operation record."""

    operation_id: str
    from_snapshot_id: str
    to_snapshot_id: str
    status: RollbackStatus = RollbackStatus.PENDING
    initiated_by: str = ""
    reason: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "from_snapshot_id": self.from_snapshot_id,
            "to_snapshot_id": self.to_snapshot_id,
            "status": self.status.value,
            "initiated_by": self.initiated_by,
            "reason": self.reason,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error": self.error,
        }


class RollbackEngine:
    """
    Safe system state restoration engine.

    Rollback Process:
    1. Load last known-good snapshot
    2. Validate snapshot integrity
    3. Halt all agent execution
    4. Restore state atomically
    5. Notify all agents of rollback
    6. Resume execution
    7. Log rollback event
    """

    def __init__(self, snapshot_dir: str = "/mcp/dev_evolution/snapshots"):
        self.snapshot_dir = Path(snapshot_dir)
        self._snapshots: Dict[str, SystemSnapshot] = {}
        self._known_good: Optional[str] = None  # ID of last known-good snapshot
        self._operations: List[RollbackOperation] = []

    # ─────────────────────────────────────────────────────────────────────
    # SNAPSHOT MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────

    def create_snapshot(
        self,
        state: Dict[str, Any],
        snapshot_type: SnapshotType = SnapshotType.CHECKPOINT,
        description: str = "",
    ) -> str:
        """Create a new system snapshot."""
        snapshot = SystemSnapshot(
            snapshot_id="",
            snapshot_type=snapshot_type,
            state=state,
            description=description,
        )

        self._snapshots[snapshot.snapshot_id] = snapshot

        return snapshot.snapshot_id

    def mark_known_good(self, snapshot_id: str) -> bool:
        """Mark a snapshot as last known-good state."""
        if snapshot_id not in self._snapshots:
            return False

        snapshot = self._snapshots[snapshot_id]
        if not snapshot.verify_integrity():
            return False

        self._known_good = snapshot_id
        return True

    def get_snapshot(self, snapshot_id: str) -> Optional[SystemSnapshot]:
        """Get snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    def get_known_good(self) -> Optional[SystemSnapshot]:
        """Get last known-good snapshot."""
        if self._known_good:
            return self._snapshots.get(self._known_good)
        return None

    # ─────────────────────────────────────────────────────────────────────
    # ROLLBACK OPERATIONS
    # ─────────────────────────────────────────────────────────────────────

    async def rollback_to_known_good(
        self, initiated_by: str, reason: str
    ) -> RollbackOperation:
        """
        Rollback to last known-good state.

        This is the primary rollback method.
        """
        if not self._known_good:
            return RollbackOperation(
                operation_id="FAILED",
                from_snapshot_id="current",
                to_snapshot_id="none",
                status=RollbackStatus.FAILED,
                error="No known-good snapshot available",
            )

        return await self.rollback_to(self._known_good, initiated_by, reason)

    async def rollback_to(
        self, snapshot_id: str, initiated_by: str, reason: str
    ) -> RollbackOperation:
        """
        Rollback to a specific snapshot.

        Process:
        1. Validate target snapshot
        2. Create current state snapshot (for recovery)
        3. Halt agents
        4. Restore state
        5. Resume agents
        6. Verify restoration
        """
        target = self._snapshots.get(snapshot_id)
        if not target:
            return RollbackOperation(
                operation_id="FAILED",
                from_snapshot_id="current",
                to_snapshot_id=snapshot_id,
                status=RollbackStatus.FAILED,
                error=f"Snapshot {snapshot_id} not found",
            )

        # Validate integrity
        if not target.verify_integrity():
            return RollbackOperation(
                operation_id="FAILED",
                from_snapshot_id="current",
                to_snapshot_id=snapshot_id,
                status=RollbackStatus.FAILED,
                error=f"Snapshot {snapshot_id} failed integrity check",
            )

        # Create operation record
        op_id = hashlib.sha256(
            f"rollback:{snapshot_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        operation = RollbackOperation(
            operation_id=op_id,
            from_snapshot_id="current",
            to_snapshot_id=snapshot_id,
            status=RollbackStatus.IN_PROGRESS,
            initiated_by=initiated_by,
            reason=reason,
            started_at=datetime.utcnow(),
        )

        try:
            # Step 1: Halt agents (would be implemented with real agent control)
            await self._halt_agents()

            # Step 2: Restore state (would write to actual system components)
            await self._restore_state(target.state)

            # Step 3: Resume agents
            await self._resume_agents()

            # Step 4: Verify
            verified = await self._verify_restoration(target.state)

            operation.status = (
                RollbackStatus.VERIFIED if verified else RollbackStatus.COMPLETED
            )
            operation.completed_at = datetime.utcnow()

        except Exception as e:
            operation.status = RollbackStatus.FAILED
            operation.error = str(e)
            operation.completed_at = datetime.utcnow()

        self._operations.append(operation)
        return operation

    async def _halt_agents(self) -> None:
        """Halt all agent execution."""
        # Would be implemented with actual agent control

    async def _restore_state(self, state: Dict[str, Any]) -> bool:
        """Restore system state from snapshot."""
        # Would write to actual system components
        return True

    async def _resume_agents(self) -> None:
        """Resume agent execution."""
        # Would be implemented with actual agent control

    async def _verify_restoration(self, expected_state: Dict[str, Any]) -> bool:
        """Verify that restoration was successful."""
        # Would compare actual state to expected state
        return True

    # ─────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────

    def save_snapshots(self) -> int:
        """Save all snapshots to disk."""
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for snapshot_id, snapshot in self._snapshots.items():
            path = self.snapshot_dir / f"{snapshot_id}.json"
            with open(path, "w") as f:
                json.dump(snapshot.to_dict(), f, indent=2, default=str)
            count += 1

        # Save metadata
        meta_path = self.snapshot_dir / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump(
                {
                    "known_good": self._known_good,
                    "snapshot_count": count,
                    "last_updated": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )

        return count

    def load_snapshots(self) -> int:
        """Load snapshots from disk."""
        if not self.snapshot_dir.exists():
            return 0

        count = 0
        for path in self.snapshot_dir.glob("*.json"):
            if path.name == "metadata.json":
                continue

            with open(path, "r") as f:
                data = json.load(f)

            snapshot = SystemSnapshot(
                snapshot_id=data["snapshot_id"],
                snapshot_type=SnapshotType(data["snapshot_type"]),
                state=data["state"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                description=data.get("description", ""),
                integrity_hash=data["integrity_hash"],
            )

            self._snapshots[snapshot.snapshot_id] = snapshot
            count += 1

        # Load metadata
        meta_path = self.snapshot_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                meta = json.load(f)
            self._known_good = meta.get("known_good")

        return count

    # ─────────────────────────────────────────────────────────────────────
    # STATUS & HISTORY
    # ─────────────────────────────────────────────────────────────────────

    def get_operations(self, limit: int = 10) -> List[RollbackOperation]:
        """Get recent rollback operations."""
        return list(reversed(self._operations[-limit:]))

    def stats(self) -> Dict[str, Any]:
        """Get rollback engine statistics."""
        return {
            "total_snapshots": len(self._snapshots),
            "known_good_id": self._known_good,
            "has_known_good": self._known_good is not None,
            "total_rollbacks": len(self._operations),
            "successful_rollbacks": sum(
                1
                for op in self._operations
                if op.status in [RollbackStatus.COMPLETED, RollbackStatus.VERIFIED]
            ),
            "failed_rollbacks": sum(
                1 for op in self._operations if op.status == RollbackStatus.FAILED
            ),
        }
