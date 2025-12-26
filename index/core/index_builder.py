"""
Index Builder — Global Index Construction and Query
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import json

from .index_schema import IndexEntry, IndexType, IndexDomain


@dataclass
class IndexQuery:
    """Query parameters for index search."""
    types: Optional[List[IndexType]] = None
    domains: Optional[List[IndexDomain]] = None
    min_confidence: float = 0.0
    max_confidence: float = 1.0
    sources: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    reality_tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class IndexBuilder:
    """
    Global index builder and query engine.
    
    Indexes:
    - agents (role, version, status)
    - prompts (hash, category, level)
    - signals (type, urgency, domain)
    - debates (participants, consensus)
    - predictions (horizon, validation)
    
    Storage:
    - In-memory index for fast queries
    - Persistent JSON files in /mcp/index/
    - Optional Firestore sync
    """
    
    def __init__(self, index_root: str = "/mcp/index"):
        self.index_root = Path(index_root)
        self._indices: Dict[IndexType, Dict[str, IndexEntry]] = {
            t: {} for t in IndexType
        }
        self._domain_indices: Dict[IndexDomain, List[str]] = {
            d: [] for d in IndexDomain
        }
        self._confidence_sorted: List[str] = []
        self._time_sorted: List[str] = []
    
    # ─────────────────────────────────────────────────────────────────────
    # INDEX OPERATIONS
    # ─────────────────────────────────────────────────────────────────────
    
    def add(self, entry: IndexEntry) -> str:
        """Add entry to index. Returns entry ID."""
        # Add to type index
        self._indices[entry.type][entry.id] = entry
        
        # Add to domain index
        if entry.id not in self._domain_indices[entry.domain]:
            self._domain_indices[entry.domain].append(entry.id)
        
        # Update sorted lists
        self._update_sorted_indices(entry)
        
        return entry.id
    
    def get(self, entry_id: str, entry_type: Optional[IndexType] = None) -> Optional[IndexEntry]:
        """Get entry by ID."""
        if entry_type:
            return self._indices[entry_type].get(entry_id)
        
        # Search all types
        for type_index in self._indices.values():
            if entry_id in type_index:
                return type_index[entry_id]
        
        return None
    
    def remove(self, entry_id: str, entry_type: IndexType) -> bool:
        """Remove entry from index."""
        if entry_id not in self._indices[entry_type]:
            return False
        
        entry = self._indices[entry_type][entry_id]
        
        # Remove from type index
        del self._indices[entry_type][entry_id]
        
        # Remove from domain index
        if entry_id in self._domain_indices[entry.domain]:
            self._domain_indices[entry.domain].remove(entry_id)
        
        # Remove from sorted lists
        if entry_id in self._confidence_sorted:
            self._confidence_sorted.remove(entry_id)
        if entry_id in self._time_sorted:
            self._time_sorted.remove(entry_id)
        
        return True
    
    def update(self, entry: IndexEntry) -> bool:
        """Update existing entry."""
        if entry.id not in self._indices[entry.type]:
            return False
        
        entry.updated_at = datetime.utcnow()
        self._indices[entry.type][entry.id] = entry
        self._update_sorted_indices(entry)
        
        return True
    
    def _update_sorted_indices(self, entry: IndexEntry) -> None:
        """Update sorted indices with new/updated entry."""
        entry_id = entry.id
        
        # Remove existing if present
        if entry_id in self._confidence_sorted:
            self._confidence_sorted.remove(entry_id)
        if entry_id in self._time_sorted:
            self._time_sorted.remove(entry_id)
        
        # Add to confidence-sorted (descending)
        inserted = False
        for i, existing_id in enumerate(self._confidence_sorted):
            existing = self.get(existing_id)
            if existing and entry.confidence > existing.confidence:
                self._confidence_sorted.insert(i, entry_id)
                inserted = True
                break
        if not inserted:
            self._confidence_sorted.append(entry_id)
        
        # Add to time-sorted (descending - newest first)
        self._time_sorted.insert(0, entry_id)
    
    # ─────────────────────────────────────────────────────────────────────
    # QUERY OPERATIONS
    # ─────────────────────────────────────────────────────────────────────
    
    def query(self, q: IndexQuery) -> List[IndexEntry]:
        """Execute query against index."""
        results = []
        
        # Determine which type indices to search
        types_to_search = q.types if q.types else list(IndexType)
        
        for entry_type in types_to_search:
            for entry in self._indices[entry_type].values():
                if self._matches_query(entry, q):
                    results.append(entry)
        
        # Apply limit and offset
        return results[q.offset:q.offset + q.limit]
    
    def _matches_query(self, entry: IndexEntry, q: IndexQuery) -> bool:
        """Check if entry matches query criteria."""
        # Domain filter
        if q.domains and entry.domain not in q.domains:
            return False
        
        # Confidence filter
        if entry.confidence < q.min_confidence or entry.confidence > q.max_confidence:
            return False
        
        # Source filter
        if q.sources and entry.source not in q.sources:
            return False
        
        # Tags filter
        if q.tags:
            if not any(tag in entry.tags for tag in q.tags):
                return False
        
        # Reality tag filter
        if q.reality_tags and entry.reality_tag not in q.reality_tags:
            return False
        
        # Time filters
        if q.created_after and entry.created_at < q.created_after:
            return False
        if q.created_before and entry.created_at > q.created_before:
            return False
        
        return True
    
    def by_type(self, entry_type: IndexType, limit: int = 100) -> List[IndexEntry]:
        """Get entries by type."""
        entries = list(self._indices[entry_type].values())
        return entries[:limit]
    
    def by_domain(self, domain: IndexDomain, limit: int = 100) -> List[IndexEntry]:
        """Get entries by domain."""
        entry_ids = self._domain_indices[domain][:limit]
        return [self.get(eid) for eid in entry_ids if self.get(eid)]
    
    def by_confidence(self, min_confidence: float = 0.8, limit: int = 100) -> List[IndexEntry]:
        """Get high-confidence entries."""
        results = []
        for entry_id in self._confidence_sorted:
            entry = self.get(entry_id)
            if entry and entry.confidence >= min_confidence:
                results.append(entry)
                if len(results) >= limit:
                    break
        return results
    
    def recent(self, limit: int = 100) -> List[IndexEntry]:
        """Get most recent entries."""
        entry_ids = self._time_sorted[:limit]
        return [self.get(eid) for eid in entry_ids if self.get(eid)]
    
    # ─────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────
    
    def save(self) -> Dict[str, int]:
        """Save all indices to disk."""
        counts = {}
        
        for entry_type in IndexType:
            type_dir = self.index_root / entry_type.value
            type_dir.mkdir(parents=True, exist_ok=True)
            
            index_file = type_dir / "index.json"
            entries = [e.to_dict() for e in self._indices[entry_type].values()]
            
            with open(index_file, "w") as f:
                json.dump(entries, f, indent=2, default=str)
            
            counts[entry_type.value] = len(entries)
        
        return counts
    
    def load(self) -> Dict[str, int]:
        """Load all indices from disk."""
        counts = {}
        
        for entry_type in IndexType:
            type_dir = self.index_root / entry_type.value
            index_file = type_dir / "index.json"
            
            if index_file.exists():
                with open(index_file, "r") as f:
                    entries_data = json.load(f)
                
                for data in entries_data:
                    entry = IndexEntry.from_dict(data)
                    self.add(entry)
                
                counts[entry_type.value] = len(entries_data)
            else:
                counts[entry_type.value] = 0
        
        return counts
    
    # ─────────────────────────────────────────────────────────────────────
    # STATISTICS
    # ─────────────────────────────────────────────────────────────────────
    
    def stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_entries": sum(len(idx) for idx in self._indices.values()),
            "by_type": {t.value: len(self._indices[t]) for t in IndexType},
            "by_domain": {d.value: len(self._domain_indices[d]) for d in IndexDomain},
            "avg_confidence": self._calculate_avg_confidence()
        }
    
    def _calculate_avg_confidence(self) -> float:
        """Calculate average confidence across all entries."""
        total = 0.0
        count = 0
        for type_index in self._indices.values():
            for entry in type_index.values():
                total += entry.confidence
                count += 1
        return total / count if count > 0 else 0.0
