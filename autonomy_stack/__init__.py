"""
Autonomy Stack - Local AI-autonomy orchestration layer
Integrates Celery, LangChain, ChromaDB, and role-based agents
"""
__version__ = "1.0.0"

from .agent_factory import AgentFactory
from .memory_layer import MemoryLayer
from .task_queue import TaskQueue
from .security import SecurityManager
from .models import AgentConfig, TaskRequest, MemoryEntry

__all__ = [
    "AgentFactory",
    "MemoryLayer",
    "TaskQueue",
    "SecurityManager",
    "AgentConfig",
    "TaskRequest",
    "MemoryEntry",
]
