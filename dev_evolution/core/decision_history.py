"""
Decision History — Immutable Log of All Decisions
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import hashlib
import json


class DecisionType(Enum):
    """Types of decisions."""
    PREDICTION = "prediction"
    STRATEGY = "strategy"
    MUTATION = "mutation"
    APPROVAL = "approval"
    REJECTION = "rejection"
    CONSENSUS = "consensus"
    VETO = "veto"
    ROLLBACK = "rollback"


class DecisionOutcome(Enum):
    """Outcome of a decision."""
    PENDING = "pending"
    EXECUTED = "executed"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    ROLLED_BACK = "rolled_back"


@dataclass
class Decision:
    """
    Immutable decision record.
    
    Once created, a decision cannot be modified.
    All changes create new decisions referencing the original.
    """
    decision_id: str
    decision_type: DecisionType
    agent_id: str
    reasoning: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    outcome: DecisionOutcome = DecisionOutcome.PENDING
    parent_decision_id: Optional[str] = None  # For decision chains
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Immutability enforcement
    _frozen: bool = field(default=False, repr=False)
    
    def __post_init__(self):
        if not self.decision_id:
            # Generate deterministic ID
            key = f"{self.decision_type.value}:{self.agent_id}:{self.timestamp.isoformat()}"
            self.decision_id = hashlib.sha256(key.encode()).hexdigest()[:16]
        
        self._frozen = True
    
    def __setattr__(self, name, value):
        if hasattr(self, '_frozen') and self._frozen and name != '_frozen':
            if name == 'outcome':
                # Outcome can be updated through proper methods
                object.__setattr__(self, name, value)
            else:
                raise AttributeError(f"Decision is immutable: cannot modify {name}")
        else:
            object.__setattr__(self, name, value)
    
    @property
    def hash(self) -> str:
        """Generate hash of decision content."""
        content = f"{self.decision_type.value}:{self.reasoning}:{self.confidence}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "agent_id": self.agent_id,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "context": self.context,
            "outcome": self.outcome.value,
            "parent_decision_id": self.parent_decision_id,
            "timestamp": self.timestamp.isoformat(),
            "hash": self.hash
        }


class DecisionHistory:
    """
    Immutable log of all system decisions.
    
    Features:
    - Append-only (no deletions)
    - Hash chain for integrity
    - Parent references for decision chains
    - Query by agent, type, outcome
    """
    
    def __init__(self):
        self._decisions: List[Decision] = []
        self._index_by_id: Dict[str, int] = {}
        self._index_by_agent: Dict[str, List[int]] = {}
        self._index_by_type: Dict[DecisionType, List[int]] = {t: [] for t in DecisionType}
        self._chain_hash: str = "GENESIS"
    
    def record(self, decision: Decision) -> str:
        """
        Record a decision to history.
        
        Returns the decision ID.
        Appends to chain — cannot be undone.
        """
        idx = len(self._decisions)
        self._decisions.append(decision)
        
        # Update indices
        self._index_by_id[decision.decision_id] = idx
        
        if decision.agent_id not in self._index_by_agent:
            self._index_by_agent[decision.agent_id] = []
        self._index_by_agent[decision.agent_id].append(idx)
        
        self._index_by_type[decision.decision_type].append(idx)
        
        # Update chain hash
        self._chain_hash = hashlib.sha256(
            f"{self._chain_hash}:{decision.hash}".encode()
        ).hexdigest()[:32]
        
        return decision.decision_id
    
    def get(self, decision_id: str) -> Optional[Decision]:
        """Get decision by ID."""
        idx = self._index_by_id.get(decision_id)
        return self._decisions[idx] if idx is not None else None
    
    def get_by_agent(self, agent_id: str) -> List[Decision]:
        """Get all decisions by an agent."""
        indices = self._index_by_agent.get(agent_id, [])
        return [self._decisions[i] for i in indices]
    
    def get_by_type(self, decision_type: DecisionType) -> List[Decision]:
        """Get all decisions of a type."""
        indices = self._index_by_type[decision_type]
        return [self._decisions[i] for i in indices]
    
    def get_chain(self, decision_id: str) -> List[Decision]:
        """Get decision chain (follow parent references)."""
        chain = []
        current = self.get(decision_id)
        
        while current:
            chain.insert(0, current)
            if current.parent_decision_id:
                current = self.get(current.parent_decision_id)
            else:
                break
        
        return chain
    
    def update_outcome(self, decision_id: str, outcome: DecisionOutcome) -> bool:
        """
        Update decision outcome.
        
        This is the only allowed modification — records outcome validation.
        """
        decision = self.get(decision_id)
        if decision:
            object.__setattr__(decision, 'outcome', outcome)
            return True
        return False
    
    def verify_integrity(self) -> bool:
        """Verify chain integrity."""
        computed_hash = "GENESIS"
        
        for decision in self._decisions:
            computed_hash = hashlib.sha256(
                f"{computed_hash}:{decision.hash}".encode()
            ).hexdigest()[:32]
        
        return computed_hash == self._chain_hash
    
    def export(self) -> List[Dict[str, Any]]:
        """Export all decisions for persistence."""
        return [d.to_dict() for d in self._decisions]
    
    def stats(self) -> Dict[str, Any]:
        """Get decision history statistics."""
        return {
            "total_decisions": len(self._decisions),
            "by_type": {t.value: len(self._index_by_type[t]) for t in DecisionType},
            "by_outcome": {
                o.value: sum(1 for d in self._decisions if d.outcome == o)
                for o in DecisionOutcome
            },
            "unique_agents": len(self._index_by_agent),
            "chain_hash": self._chain_hash,
            "integrity_valid": self.verify_integrity()
        }
