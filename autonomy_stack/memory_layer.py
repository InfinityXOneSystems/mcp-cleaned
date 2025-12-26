"""
Memory layer using ChromaDB for vector storage and context management
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os
from .models import MemoryEntry

logger = logging.getLogger(__name__)


class MemoryLayer:
    """ChromaDB-based vector memory for context persistence"""

    def __init__(self, persist_dir: str = "./data/chroma"):
        """Initialize ChromaDB memory layer"""
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize Chroma client with persistence
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir,
            anonymized_telemetry=False,
        )
        self.client = chromadb.Client(settings)
        
        # Initialize collections for different agent roles
        self.collections = {
            "visionary": self.client.get_or_create_collection("visionary_memory"),
            "strategist": self.client.get_or_create_collection("strategist_memory"),
            "builder": self.client.get_or_create_collection("builder_memory"),
            "critic": self.client.get_or_create_collection("critic_memory"),
            "shared": self.client.get_or_create_collection("shared_memory"),
        }
        logger.info("✓ ChromaDB memory layer initialized")

    def store(
        self,
        entry: MemoryEntry,
        collection: str = "shared"
    ) -> bool:
        """Store a memory entry with embedding"""
        try:
            col = self.collections.get(collection) or self.collections["shared"]
            
            metadata = entry.metadata.copy()
            metadata["agent_role"] = entry.agent_role
            metadata["timestamp"] = entry.timestamp.isoformat()
            
            col.add(
                ids=[entry.id],
                documents=[entry.content],
                metadatas=[metadata],
                embeddings=[entry.embedding] if entry.embedding else None,
            )
            logger.debug(f"✓ Stored memory: {entry.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False

    def retrieve(
        self,
        query: str,
        collection: str = "shared",
        n_results: int = 5,
        agent_role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories by semantic similarity"""
        try:
            col = self.collections.get(collection) or self.collections["shared"]
            
            where_filter = None
            if agent_role:
                where_filter = {"agent_role": {"$eq": agent_role}}
            
            results = col.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances", "embeddings"]
            )
            
            # Format results
            memories = []
            if results["documents"]:
                for doc, metadata, distance in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    memories.append({
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1 - (distance / 2),  # Convert distance to similarity
                    })
            
            return memories
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return []

    def store_task_result(
        self,
        task_id: str,
        agent_role: str,
        objective: str,
        result: Any,
        confidence: float,
        reasoning: str
    ) -> bool:
        """Store task execution result for future reference"""
        entry = MemoryEntry(
            id=task_id,
            content=f"Objective: {objective}\n\nResult: {str(result)}\n\nReasoning: {reasoning}",
            metadata={
                "task_id": task_id,
                "objective": objective,
                "confidence": confidence,
                "reasoning": reasoning,
            },
            agent_role=agent_role,
            timestamp=datetime.now(),
        )
        return self.store(entry, collection=agent_role)

    def get_agent_context(
        self,
        agent_role: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent context for an agent"""
        try:
            col = self.collections.get(agent_role) or self.collections["shared"]
            
            # Get all documents (ChromaDB doesn't support ordering by date directly)
            results = col.get(
                include=["documents", "metadatas"],
                limit=limit
            )
            
            memories = []
            if results["documents"]:
                for doc, metadata in zip(results["documents"], results["metadatas"]):
                    memories.append({
                        "content": doc,
                        "metadata": metadata,
                    })
            
            return memories
        except Exception as e:
            logger.error(f"Failed to get agent context: {e}")
            return []

    def clear_collection(self, collection: str = "shared") -> bool:
        """Clear all entries in a collection"""
        try:
            col = self.collections.get(collection)
            if col:
                # Delete collection and recreate
                self.client.delete_collection(collection)
                self.collections[collection] = self.client.get_or_create_collection(collection)
                logger.info(f"✓ Cleared collection: {collection}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False

    def export_memory(self, collection: str = "shared") -> Dict[str, Any]:
        """Export collection data"""
        try:
            col = self.collections.get(collection) or self.collections["shared"]
            data = col.get(include=["documents", "metadatas", "embeddings"])
            return {
                "collection": collection,
                "count": len(data["documents"]) if data["documents"] else 0,
                "data": data,
            }
        except Exception as e:
            logger.error(f"Failed to export memory: {e}")
            return {}

    def get_memory_stats(self) -> Dict[str, int]:
        """Get statistics for all collections"""
        stats = {}
        for name, col in self.collections.items():
            try:
                count = col.count()
                stats[name] = count
            except Exception as e:
                logger.error(f"Failed to count {name}: {e}")
                stats[name] = 0
        return stats
