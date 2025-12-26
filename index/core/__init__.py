"""
Index System — Global Intelligence Index
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md

Indexes: agents, prompts, signals, debates, predictions
Indexed by: time, confidence, source, domain
"""

from .index_builder import IndexBuilder
from .index_schema import IndexEntry, IndexType

__all__ = ["IndexBuilder", "IndexEntry", "IndexType"]
