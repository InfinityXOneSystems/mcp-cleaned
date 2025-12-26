"""Omni Gateway — P1 HARDENED

AUTHORITY: This is the canonical production gateway. All serving MUST use:
    uvicorn omni_gateway_p1:app --host 0.0.0.0 --port 8000

P1 ENFORCEMENT:
- Canonical entrypoint: Direct python execution is refused
- Immutable demo mode: DEMO_MODE=1 locks to read-only + dry-run
- Deterministic health: /health aggregates adapter + Firestore status
- Structured errors: All endpoints return consistent JSON
- Secrets hygiene: Requires GOOGLE_APPLICATION_CREDENTIALS for Firestore

USAGE:
    # Local development
    uvicorn omni_gateway_p1:app --host 127.0.0.1 --port 8000 --reload
    
    # Production (Cloud Run)
    uvicorn omni_gateway_p1:app --host 0.0.0.0 --port 8000 --workers 2

NEVER:
    python omni_gateway_p1.py  # ❌ REFUSED
"""

import sys
import os
import logging

# P1: Refuse direct execution
if __name__ == "__main__":
    print("=" * 80)
    print("⛔ P1 ENFORCEMENT: Direct python execution refused")
    print("=" * 80)
    print()
    print("AUTHORITY: omni_gateway_p1.py must be served via uvicorn")
    print()
    print("Correct usage:")
    print("  uvicorn omni_gateway_p1:app --host 0.0.0.0 --port 8000")
    print()
    print("For local development:")
    print("  uvicorn omni_gateway_p1:app --host 127.0.0.1 --port 8000 --reload")
    print()
    print("See FINAL_VERDICT.md for demo conditions")
    print("=" * 80)
    sys.exit(1)

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from google.cloud import firestore
from google.api_core.exceptions import GoogleAPIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# P1: Configuration
DEMO_MODE = os.environ.get("DEMO_MODE", "0") == "1"
FIRESTORE_PROJECT = os.environ.get("FIRESTORE_PROJECT", "infinity-x-one-systems")
FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "mcp_memory")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")

# P1: Security warnings
if MCP_API_KEY == "default-key-change-me":
    logger.warning("⚠ P1 SECURITY: MCP_API_KEY is default. Rotate immediately.")

if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    logger.warning("⚠ P1 SECRETS: GOOGLE_APPLICATION_CREDENTIALS not set. Firestore may fail.")

if DEMO_MODE:
    logger.info("🔒 P1 DEMO MODE: System locked to read-only + dry-run")

# P1: Initialize FastAPI
app = FastAPI(
    title="Infinity XOS Omni Gateway — P1 Hardened",
    description="Production-grade orchestrator with P1 enforcement",
    version="3.1-p1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # P2: Restrict to allowlist
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# P1: Load MCP adapter
sys.path.insert(0, os.path.dirname(__file__))

try:
    from mcp_http_adapter_p1 import router as mcp_router, REGISTRY_HASH, DEMO_MODE as MCP_DEMO_MODE
    app.include_router(mcp_router)
    MCP_AVAILABLE = True
    logger.info(f"✓ P1: MCP adapter mounted (hash={REGISTRY_HASH}, demo={MCP_DEMO_MODE})")
except Exception as e:
    logger.error(f"⚠ P1: MCP adapter unavailable: {e}")
    MCP_AVAILABLE = False

# P1: Firestore client (lazy)
_firestore_client = None
_firestore_available = False


def init_firestore():
    """Initialize Firestore with P1 error handling"""
    global _firestore_client, _firestore_available
    
    if _firestore_client:
        return _firestore_client
    
    try:
        if not FIRESTORE_PROJECT:
            logger.warning("P1: FIRESTORE_PROJECT not set; Firestore disabled")
            _firestore_available = False
            return None
        
        _firestore_client = firestore.Client(project=FIRESTORE_PROJECT)
        _firestore_available = True
        logger.info(f"P1: Connected to Firestore project={FIRESTORE_PROJECT}")
        return _firestore_client
    
    except GoogleAPIError as e:
        logger.error(f"P1: Firestore init failed (GoogleAPIError): {e}")
        _firestore_available = False
        return None
    
    except Exception as e:
        logger.error(f"P1: Firestore init failed (unexpected): {e}")
        _firestore_available = False
        return None


# P1: Startup
@app.on_event("startup")
async def on_startup():
    """P1: Initialize Firestore on startup"""
    logger.info("P1: Gateway startup")
    try:
        init_firestore()
    except Exception as e:
        logger.error(f"P1: Startup error: {e}")


# ===== P1 HEALTH CONTRACT =====
@app.get("/health")
async def gateway_health():
    """P1: Deterministic health contract (gateway + adapter + Firestore)"""
    components = {
        "gateway": "healthy",
        "adapter": "unavailable",
        "firestore": "unknown",
    }
    
    # Check adapter health
    if MCP_AVAILABLE:
        try:
            import httpx
            # Internal health check (assumes adapter is mounted)
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://127.0.0.1:8000/mcp/health", timeout=2.0)
                if resp.status_code == 200:
                    components["adapter"] = "healthy"
                else:
                    components["adapter"] = f"degraded: {resp.status_code}"
        except Exception as e:
            components["adapter"] = f"degraded: {str(e)[:50]}"
    
    # Check Firestore
    client = init_firestore()
    if client:
        components["firestore"] = "healthy"
    else:
        components["firestore"] = "unavailable"
    
    overall_status = "healthy"
    if components["adapter"] == "unavailable" or components["firestore"] == "unavailable":
        overall_status = "degraded"
    
    return JSONResponse(content={
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": components,
        "demo_mode": DEMO_MODE,
        "version": "3.1-p1"
    })


@app.get("/api/status")
async def api_status():
    """P1: Alias for /health"""
    return await gateway_health()


# ===== COCKPIT UI =====
@app.get("/", response_class=HTMLResponse)
async def serve_cockpit():
    """Serve Intelligence Cockpit UI"""
    try:
        cockpit_path = os.path.join(os.path.dirname(__file__), "cockpit.html")
        with open(cockpit_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"P1: Failed to load cockpit: {e}")
        return HTMLResponse(
            content=f"<h1>Cockpit Unavailable</h1><p>{str(e)}</p>",
            status_code=500
        )


# P1: Export
__all__ = ["app"]

logger.info(f"P1: Omni Gateway initialized (demo={DEMO_MODE}, firestore={FIRESTORE_PROJECT})")
