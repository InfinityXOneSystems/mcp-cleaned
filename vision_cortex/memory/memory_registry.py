"""Registry for memory backends (Firestore, embeddings, episodic logs).

Provides production-friendly adapters with an in-memory fallback so tests and
local runs do not require cloud credentials.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


class FirestoreClient(Protocol):
    def write(self, collection: str, doc: Dict[str, Any]) -> None: ...

    def query(self, collection: str, **kwargs: Any) -> Any: ...


class VectorStore(Protocol):
    def add(self, text: str, metadata: Dict[str, Any]) -> str: ...

    def search(self, query: str, k: int = 5) -> Any: ...


@dataclass
class MemoryRegistry:
    firestore: FirestoreClient
    vector_store: VectorStore
    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("vision_cortex.memory")
    )

    def persist_event(self, doc: Dict[str, Any]) -> None:
        try:
            self.firestore.write("mcp_memory", doc)
        except Exception as exc:
            self.logger.error("Persist event failed: %s", exc)
            raise

    def add_embedding(self, text: str, metadata: Dict[str, Any]) -> str:
        try:
            return self.vector_store.add(text=text, metadata=metadata)
        except Exception as exc:
            self.logger.error("Add embedding failed: %s", exc)
            raise

    def search_embeddings(self, query: str, k: int = 5) -> Any:
        return self.vector_store.search(query=query, k=k)


class InMemoryFirestore(FirestoreClient):
    """Simple in-memory store for tests and local runs."""

    def __init__(self) -> None:
        self._collections: Dict[str, List[Dict[str, Any]]] = {}

    def write(self, collection: str, doc: Dict[str, Any]) -> None:
        self._collections.setdefault(collection, []).append(doc)

    def query(self, collection: str, **kwargs: Any) -> Any:
        return list(self._collections.get(collection, []))


class InMemoryVectorStore(VectorStore):
    """Toy vector store that keeps text and metadata for retrieval tests."""

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def add(self, text: str, metadata: Dict[str, Any]) -> str:
        record_id = f"vec-{len(self._records)+1}"
        self._records.append(
            {"id": record_id, "text": text, "metadata": metadata, "ts": time.time()}
        )
        return record_id

    def search(self, query: str, k: int = 5) -> Any:
        # Naive search: return most recent k entries containing any query token.
        tokens = set(query.lower().split())
        scored: List[Dict[str, Any]] = []
        for rec in self._records:
            text_tokens = set(rec["text"].lower().split())
            overlap = tokens & text_tokens
            score = len(overlap)
            scored.append({"record": rec, "score": score})
        scored.sort(key=lambda r: (r["score"], r["record"]["ts"]), reverse=True)
        return scored[:k]


def build_memory_registry() -> MemoryRegistry:
    """Factory that prefers Firestore if available, otherwise in-memory."""

    try:
        from google.cloud import firestore  # type: ignore

        client = firestore.Client()

        class FirestoreAdapter(FirestoreClient):
            def write(self, collection: str, doc: Dict[str, Any]) -> None:
                client.collection(collection).add(doc)

            def query(self, collection: str, **kwargs: Any) -> Any:
                col = client.collection(collection)
                # Basic passthrough; more filters can be layered as needed.
                docs = col.stream()
                return [d.to_dict() for d in docs]

        registry = MemoryRegistry(
            firestore=FirestoreAdapter(), vector_store=InMemoryVectorStore()
        )
        registry.logger.info("Using Firestore-backed MemoryRegistry")
        return registry
    except Exception:
        registry = MemoryRegistry(
            firestore=InMemoryFirestore(), vector_store=InMemoryVectorStore()
        )
        registry.logger.info("Using InMemory MemoryRegistry (Firestore unavailable)")
        return registry
