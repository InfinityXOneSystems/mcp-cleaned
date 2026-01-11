"""
Data models for autonomy stack
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Available agent roles"""

    VISIONARY = "visionary"
    STRATEGIST = "strategist"
    BUILDER = "builder"
    CRITIC = "critic"


class TaskStatus(str, Enum):
    """Task lifecycle states"""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentConfig(BaseModel):
    """Configuration for agent initialization"""

    role: AgentRole
    model: str = Field(default="gpt-4-turbo-preview")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1)
    tools: List[str] = Field(default_factory=list)
    memory_size: int = Field(default=10)
    governance_level: str = Field(default="MEDIUM")

    class Config:
        use_enum_values = True


class TaskRequest(BaseModel):
    """Request to execute a task"""

    task_type: str
    agent_role: AgentRole
    objective: str
    context: Optional[Dict[str, Any]] = None
    priority: int = Field(default=5, ge=1, le=10)
    timeout_seconds: int = Field(default=300)
    require_approval: bool = Field(default=False)

    class Config:
        use_enum_values = True


class TaskResult(BaseModel):
    """Result of task execution"""

    task_id: str
    status: TaskStatus
    agent_role: str
    objective: str
    result: Any
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    execution_time_ms: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        use_enum_values = True


class MemoryEntry(BaseModel):
    """Entry in vector memory"""

    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    agent_role: Optional[str] = None
    timestamp: datetime
    relevance_score: Optional[float] = None

    class Config:
        use_enum_values = True


class PipelineConfig(BaseModel):
    """Configuration for a multi-agent pipeline"""

    name: str
    agents: List[AgentRole]
    stages: List[Dict[str, Any]]
    requires_consensus: bool = Field(default=False)
    timeout_seconds: int = Field(default=600)

    class Config:
        use_enum_values = True


class ModelExperimentConfig(BaseModel):
    """Configuration for model experimentation"""

    name: str
    model_type: str  # "pytorch", "tensorflow", "huggingface"
    task: str
    parameters: Dict[str, Any]
    datasets: List[str]
    metrics: List[str]
    batch_size: int = Field(default=32)
    epochs: int = Field(default=10)
