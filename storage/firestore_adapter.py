import os
from datetime import datetime
from typing import Dict, Any
try:
    from google.cloud import firestore
except Exception:
    firestore = None

class FirestoreAdapter:
    def __init__(self, client=None):
        if client:
            self.client = client
        elif firestore:
            self.client = firestore.Client()
        else:
            self.client = None

    def write_memory(self, doc: Dict[str, Any], collection: str = "mcp_memory"):
        if not self.client:
            # fallback: write to local file for dev
            path = os.environ.get("FIRESTORE_LOCAL", "crawler/output/normalized_firestone.json")
            import json
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"collection": collection, "doc": doc, "written_at": datetime.utcnow().isoformat()}) + "\n")
            return
        col = self.client.collection(collection)
        doc_id = doc.get("session_hash") or f"auto_{int(datetime.utcnow().timestamp())}"
        col.document(doc_id).set(doc, merge=True)
