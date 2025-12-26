from fastapi import FastAPI, HTTPException, Body, Depends, Header
from pydantic import BaseModel
import os
from typing import Optional, List, Dict
from datetime import datetime
from storage.firestore_adapter import FirestoreAdapter

app = FastAPI()
fs = FirestoreAdapter()

class CrawlRequest(BaseModel):
    seed_file: str

class LeadQuery(BaseModel):
    industry: Optional[str] = None
    top_k: int = 25

def check_admin(authorization: Optional[str] = Header(None)):
    token = os.getenv("ADMIN_TOKEN")
    if not token:
        return True
    if not authorization or not authorization.startswith("Bearer " + token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

@app.post("/crawl")
async def crawl(req: CrawlRequest = Body(...), auth=Depends(check_admin)):
    # trigger background crawl (implementation: spawn subprocess or task)
    # minimal: persist request to memory for agents to pick up
    doc = {"session_hash": f"crawl_{int(datetime.utcnow().timestamp())}", "type": "crawl_request", "content": req.dict(), "created_at": datetime.utcnow().isoformat()}
    fs.write_memory(doc)
    return {"queued": True, "seed": req.seed_file}

@app.post("/admin/doc/ingest")
async def ingest_doc(payload: Dict = Body(...), auth=Depends(check_admin)):
    doc = {"session_hash": payload.get("session_hash") or f"ingest_{int(datetime.utcnow().timestamp())}", "type": "ingest", "content": payload, "created_at": datetime.utcnow().isoformat()}
    fs.write_memory(doc)
    return {"ok": True}
