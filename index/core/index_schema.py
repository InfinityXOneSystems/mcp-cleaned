"""
Index Schema — Canonical Index Entry Structure
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import hashlib


class IndexType(Enum):
    """Canonical index entry types."""
    AGENT = "agent"
    PROMPT = "prompt"
    SIGNAL = "signal"
    DEBATE = "debate"
    PREDICTION = "prediction"
    CONSENSUS = "consensus"
    MUTATION = "mutation"


class IndexDomain(Enum):
    """Strategic seed domains."""
    ECONOMICS = "economics"
    AI = "ai"
    ENERGY = "energy"
    GOVERNANCE = "governance"
    PHILOSOPHY = "philosophy"
    SYSTEMS = "systems"
    TECHNOLOGY = "technology"
    CULTURE = "culture"


@dataclass
class IndexEntry:
    """
    Canonical index entry structure.
    
    All indexed items MUST conform to this schema.
    """
    id: str
    type: IndexType
    content: Dict[str, Any]
    confidence: float
    source: str  # crawler, ingestor, predictor, external
    domain: IndexDomain
    
    # Temporal indexing
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Classification
    tags: List[str] = field(default_factory=list)
    
    # Provenance
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Reality discipline tags
    reality_tag: Optional[str] = None  # REAL-TODAY, EMERGING, HYPOTHETICAL, UNCERTAIN
    
    def __post_init__(self):
        if not self.id:
            # Generate deterministic ID
            key = f"{self.type.value}:{self.source}:{self.created_at.isoformat()}"
            self.id = hashlib.sha256(key.encode()).hexdigest()[:16]
        
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
    
    @property
    def index_key(self) -> str:
        """Generate index key for fast lookup."""
        return f"{self.type.value}:{self.domain.value}:{self.id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "confidence": self.confidence,
            "source": self.source,
            "domain": self.domain.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "reality_tag": self.reality_tag,
            "index_key": self.index_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexEntry":
        """Create IndexEntry from dictionary."""
        return cls(
            id=data["id"],
            type=IndexType(data["type"]),
            content=data["content"],
            confidence=data["confidence"],
            source=data["source"],
            domain=IndexDomain(data["domain"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            tags=data.get("tags", []),
            agent_id=data.get("agent_id"),
            session_id=data.get("session_id"),
            reality_tag=data.get("reality_tag")
        )


@dataclass
class AgentIndexEntry(IndexEntry):
    """Index entry for agents."""
    role: str = ""
    version: str = ""
    governance_level: str = ""
    
    def __post_init__(self):
        self.type = IndexType.AGENT
        super().__post_init__()


@dataclass
class PromptIndexEntry(IndexEntry):
    """Index entry for prompts."""
    prompt_hash: str = ""
    category: str = ""
    autonomy_level: int = 0
    
    def __post_init__(self):
        self.type = IndexType.PROMPT
        super().__post_init__()


@dataclass
class SignalIndexEntry(IndexEntry):
    """Index entry for signals."""
    signal_type: str = ""  # weak, moderate, strong
    urgency: str = ""  # low, medium, high, critical
    
    def __post_init__(self):
        self.type = IndexType.SIGNAL
        super().__post_init__()


@dataclass
class DebateIndexEntry(IndexEntry):
    """Index entry for debates."""
    debate_id: str = ""
    participants: List[str] = field(default_factory=list)
    rounds: int = 0
    consensus_reached: bool = False
    
    def __post_init__(self):
        self.type = IndexType.DEBATE
        super().__post_init__()


@dataclass
class PredictionIndexEntry(IndexEntry):
    """Index entry for predictions."""
    prediction_id: str = ""
    horizon: str = ""  # short, medium, long
    validated: bool = False
    accuracy: Optional[float] = None
    
    def __post_init__(self):
        self.type = IndexType.PREDICTION
        super().__post_init__()
