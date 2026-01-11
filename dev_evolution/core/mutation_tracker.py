"""
Mutation Tracker — Track System Changes Over Time
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MutationType(Enum):
    """Types of system mutations."""

    PROMPT_CHANGE = "prompt_change"
    WEIGHT_ADJUSTMENT = "weight_adjustment"
    THRESHOLD_CHANGE = "threshold_change"
    ARCHITECTURAL = "architectural"
    CONFIG_CHANGE = "config_change"
    AGENT_BEHAVIOR = "agent_behavior"


class MutationStatus(Enum):
    """Status of a mutation."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    APPLIED = "applied"
    VALIDATED = "validated"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


@dataclass
class Mutation:
    """
    System mutation record.

    Tracks all changes to system configuration, prompts, weights, etc.
    """

    mutation_id: str
    mutation_type: MutationType
    agent_id: str  # Agent that proposed the mutation
    description: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    status: MutationStatus = MutationStatus.PROPOSED
    approved_by: Optional[str] = None  # human, ceo, validator
    confidence: float = 0.0
    rollback_safe: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)
    applied_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.mutation_id:
            key = f"{self.mutation_type.value}:{self.agent_id}:{self.timestamp.isoformat()}"
            self.mutation_id = hashlib.sha256(key.encode()).hexdigest()[:16]

    @property
    def diff(self) -> Dict[str, Any]:
        """Generate diff between before and after states."""
        added = {}
        removed = {}
        changed = {}

        before_keys = set(self.before_state.keys())
        after_keys = set(self.after_state.keys())

        for key in after_keys - before_keys:
            added[key] = self.after_state[key]

        for key in before_keys - after_keys:
            removed[key] = self.before_state[key]

        for key in before_keys & after_keys:
            if self.before_state[key] != self.after_state[key]:
                changed[key] = {
                    "before": self.before_state[key],
                    "after": self.after_state[key],
                }

        return {"added": added, "removed": removed, "changed": changed}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "mutation_type": self.mutation_type.value,
            "agent_id": self.agent_id,
            "description": self.description,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "status": self.status.value,
            "approved_by": self.approved_by,
            "confidence": self.confidence,
            "rollback_safe": self.rollback_safe,
            "timestamp": self.timestamp.isoformat(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "rolled_back_at": (
                self.rolled_back_at.isoformat() if self.rolled_back_at else None
            ),
            "diff": self.diff,
        }


class MutationTracker:
    """
    Tracks all system mutations.

    Features:
    - Propose mutations (requires approval)
    - Apply approved mutations
    - Track mutation history
    - Support rollback
    """

    def __init__(self):
        self._mutations: Dict[str, Mutation] = {}
        self._history: List[str] = []  # Ordered list of mutation IDs
        self._rollback_stack: List[str] = []  # Mutations that can be rolled back

    def propose(self, mutation: Mutation) -> str:
        """
        Propose a mutation.

        Mutations start in PROPOSED status and require approval.
        """
        mutation.status = MutationStatus.PROPOSED
        self._mutations[mutation.mutation_id] = mutation
        self._history.append(mutation.mutation_id)

        return mutation.mutation_id

    def approve(self, mutation_id: str, approved_by: str) -> bool:
        """Approve a proposed mutation."""
        mutation = self._mutations.get(mutation_id)

        if not mutation or mutation.status != MutationStatus.PROPOSED:
            return False

        mutation.status = MutationStatus.APPROVED
        mutation.approved_by = approved_by

        return True

    def reject(self, mutation_id: str, reason: str) -> bool:
        """Reject a proposed mutation."""
        mutation = self._mutations.get(mutation_id)

        if not mutation or mutation.status != MutationStatus.PROPOSED:
            return False

        mutation.status = MutationStatus.REJECTED

        return True

    def apply(self, mutation_id: str) -> bool:
        """
        Apply an approved mutation.

        The actual application is handled externally.
        This just tracks the status.
        """
        mutation = self._mutations.get(mutation_id)

        if not mutation or mutation.status != MutationStatus.APPROVED:
            return False

        mutation.status = MutationStatus.APPLIED
        mutation.applied_at = datetime.utcnow()

        if mutation.rollback_safe:
            self._rollback_stack.append(mutation_id)

        return True

    def validate(self, mutation_id: str) -> bool:
        """Mark a mutation as validated (successful)."""
        mutation = self._mutations.get(mutation_id)

        if not mutation or mutation.status != MutationStatus.APPLIED:
            return False

        mutation.status = MutationStatus.VALIDATED

        return True

    def rollback(self, mutation_id: str) -> Optional[Dict[str, Any]]:
        """
        Rollback a mutation.

        Returns the before_state for restoration.
        """
        mutation = self._mutations.get(mutation_id)

        if not mutation:
            return None

        if not mutation.rollback_safe:
            return None

        if mutation.status not in [MutationStatus.APPLIED, MutationStatus.VALIDATED]:
            return None

        mutation.status = MutationStatus.ROLLED_BACK
        mutation.rolled_back_at = datetime.utcnow()

        if mutation_id in self._rollback_stack:
            self._rollback_stack.remove(mutation_id)

        return mutation.before_state

    def get(self, mutation_id: str) -> Optional[Mutation]:
        """Get mutation by ID."""
        return self._mutations.get(mutation_id)

    def get_by_status(self, status: MutationStatus) -> List[Mutation]:
        """Get mutations by status."""
        return [m for m in self._mutations.values() if m.status == status]

    def get_by_type(self, mutation_type: MutationType) -> List[Mutation]:
        """Get mutations by type."""
        return [m for m in self._mutations.values() if m.mutation_type == mutation_type]

    def get_pending_approval(self) -> List[Mutation]:
        """Get mutations pending approval."""
        return self.get_by_status(MutationStatus.PROPOSED)

    def get_rollback_candidates(self) -> List[Mutation]:
        """Get mutations that can be rolled back."""
        return [self._mutations[mid] for mid in self._rollback_stack]

    def history(self, limit: int = 100) -> List[Mutation]:
        """Get mutation history (most recent first)."""
        ids = list(reversed(self._history[-limit:]))
        return [self._mutations[mid] for mid in ids]

    def stats(self) -> Dict[str, Any]:
        """Get mutation statistics."""
        return {
            "total_mutations": len(self._mutations),
            "by_status": {s.value: len(self.get_by_status(s)) for s in MutationStatus},
            "by_type": {t.value: len(self.get_by_type(t)) for t in MutationType},
            "rollback_stack_size": len(self._rollback_stack),
            "pending_approval": len(self.get_pending_approval()),
        }
