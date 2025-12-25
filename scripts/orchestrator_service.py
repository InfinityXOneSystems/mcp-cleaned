#!/usr/bin/env python3
"""Orchestrator service exposing GPT-controllable endpoints.

Endpoints: /health, /read, /write, /analyze, /simulate, /predict, /crawl
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="Orchestrator", version="1.0")
GATEWAY = os.environ.get("GATEWAY_URL", "http://localhost:8000")

class ReadRequest(BaseModel):
    target: str

class WriteRequest(BaseModel):
    target: str
    content: str

class AnalyzeRequest(BaseModel):
    payload: dict
    provider: str | None = None
    action: str | None = None

class PredictRequest(BaseModel):
    model: str
    input: dict

class CrawlRequest(BaseModel):
    url: str
    depth: int = 1
    provider: str | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/read")
def read(req: ReadRequest):
    # Placeholder: delegate to gateway read endpoint if available
    return {"status": "ok", "target": req.target, "note": "Read stub"}

@app.post("/write")
def write(req: WriteRequest):
    # Placeholder: add real write once target store is defined
    return {"status": "ok", "target": req.target, "note": "Write stub"}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    # Route by provider/action; stub hooks for GitHub/GCP/Workspace/Hostinger
    return {
        "status": "ok",
        "provider": req.provider or "generic",
        "action": req.action or "analyze",
        "analysis": req.payload
    }

@app.post("/simulate")
def simulate(req: AnalyzeRequest):
    return {
        "status": "ok",
        "provider": req.provider or "generic",
        "action": req.action or "simulate",
        "simulation": req.payload
    }

@app.post("/predict")
def predict(req: PredictRequest):
    r = requests.post(f"{GATEWAY}/predict", json={"model": req.model, "input": req.input}, timeout=15)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()

@app.post("/crawl")
def crawl(req: CrawlRequest):
    r = requests.post(f"{GATEWAY}/crawl", json={"url": req.url, "depth": req.depth}, timeout=30)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json() if r.headers.get('content-type','').startswith('application/json') else {"status": r.status_code, "body": r.text[:200]}

def serve():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))

if __name__ == "__main__":
    serve()
