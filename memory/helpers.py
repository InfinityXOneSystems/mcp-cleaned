import hashlib
from typing import Dict, Any
import logging
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parents[1] / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)


def canonical_id(content: Dict[str,Any]) -> str:
    s = json.dumps(content, sort_keys=True)
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def embed_stub(text: str) -> list:
    # placeholder: returns deterministic pseudo-embedding
    h = hashlib.sha1(text.encode('utf-8')).hexdigest()
    # split into numbers
    vec = [int(h[i:i+4],16)%1000/1000.0 for i in range(0,32,4)]
    return vec


def write_local_memory(doc: Dict[str,Any]) -> str:
    cid = canonical_id(doc)
    doc_path = DATA_DIR / f"{cid}.json"
    doc['created_at'] = datetime.utcnow().isoformat() + 'Z'
    # ensure approval fields exist
    if 'requires_approval' not in doc:
        doc['requires_approval'] = doc.get('requires_approval', False)
    if 'approval_status' not in doc:
        doc['approval_status'] = doc.get('approval_status', 'pending')
    if 'approval_metadata' not in doc:
        doc['approval_metadata'] = doc.get('approval_metadata', {})
    with open(doc_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return cid


def dedupe_and_prepare(doc: Dict[str,Any]) -> Dict[str,Any]:
    # compute canonical id and embedding for text fields
    content_text = ' '.join([str(v) for v in doc.get('content', {}).values()])
    doc['embedding'] = embed_stub(content_text)
    doc['canonical_id'] = canonical_id(doc)
    return doc
