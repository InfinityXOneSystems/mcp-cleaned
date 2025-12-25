"""
Unified API Gateway - Single entry point for all Infinity XOS endpoints
Routes /predict, /crawl, /simulate across all systems with compliance enforcement
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from enum import Enum

from compliance import compliance_validator, validate_request_middleware, get_compliance_status
from prediction_engine import log_prediction
from crawler import crawl

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Infinity XOS - Unified Gateway",
    description="Central router for /predict, /crawl, /simulate across all systems",
    version="1.0.0"
)

# CORS - Allow Horizons and all local apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = 'mcp_memory.db'

# Service URLs
SERVICES = {
    "dashboard": "http://localhost:8001",
    "intelligence": "http://localhost:8002",
    "meta": "http://localhost:8003",
    "mcp": "http://localhost:8004",  # Will be Cloud Run once deployed
}

class OperationType(Enum):
    """Unified operation types across all systems"""
    PREDICT = "predict"      # Forecasting, modeling, predictions
    CRAWL = "crawl"          # Web scraping, data collection
    SIMULATE = "simulate"    # Backtesting, scenario analysis
    READ = "read"            # Data retrieval
    ANALYZE = "analyze"      # Data analysis
    WRITE = "write"          # Data modification
    CREATE = "create"        # New resource creation
    DELETE = "delete"        # Resource deletion

@app.on_event("startup")
async def startup():
    """Initialize gateway"""
    logger.info("🚀 Infinity XOS Gateway starting...")
    logger.info(f"📡 Services: {list(SERVICES.keys())}")
    logger.info("✓ Compliance enforcement: ACTIVE")

@app.get("/health")
async def health():
    """Gateway health check"""
    return {
        "status": "healthy",
        "service": "infinity-xos-gateway",
        "timestamp": datetime.now().isoformat(),
        "compliance": "enforced"
    }

@app.get("/compliance/status")
async def compliance_status():
    """Get compliance status"""
    return get_compliance_status()

@app.get("/compliance/audit-log")
async def compliance_audit_log(limit: int = 100):
    """Get recent compliance violations"""
    return {
        "violations": compliance_validator.get_audit_log(limit),
        "total": len(compliance_validator.violation_log)
    }

# ===== UNIFIED /predict ENDPOINT =====

@app.post("/predict")
async def unified_predict(
    request: Request,
    asset: str,
    asset_type: str = "stock",
    prediction_type: str = "price",
    timeframe: str = "24h",
    target_date: str = None,
    confidence: int = 50,
    data_sources: Optional[List[str]] = None,
    user_id: Optional[str] = Header(None)
):
    """
    Unified predict endpoint
    Calls prediction engine across all systems
    
    Args:
        asset: Ticker/Symbol (TSLA, BTC, etc.)
        asset_type: crypto, stock, forex, commodity
        prediction_type: price, direction, volatility, event
        timeframe: 1h, 4h, 24h, 7d, 30d, 90d
        target_date: ISO date when prediction resolves
        confidence: 0-100 confidence score
        data_sources: Sources used (optional)
        user_id: Optional user identifier for audit
    """
    try:
        # Compliance check
        violation = await validate_request_middleware(
            "google",
            "predict",
            {
                "asset": asset,
                "type": asset_type,
                "timeframe": timeframe
            },
            dict(request.headers),
            user_id
        )
        if violation:
            return JSONResponse(status_code=403, content=violation)
        
        # Rate limit check
        if not compliance_validator.check_rate_limit("google", "read"):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Log to database
        pred_id = log_prediction(
            asset=asset,
            asset_type=asset_type,
            prediction_type=prediction_type,
            timeframe=timeframe,
            target_date=target_date or datetime.now().isoformat().split('T')[0],
            confidence=confidence,
            rationale=f"Gateway prediction request for {asset}",
            data_sources=data_sources or []
        )
        
        # Route to appropriate services based on asset type
        responses = []
        
        # 1. Call Intelligence API for sentiment/data
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                intel_response = await client.post(
                    f"{SERVICES['intelligence']}/api/intelligence/predict",
                    json={
                        "asset": asset,
                        "asset_type": asset_type,
                        "timeframe": timeframe
                    }
                )
                if intel_response.status_code == 200:
                    responses.append({"source": "intelligence", "data": intel_response.json()})
        except Exception as e:
            logger.warning(f"Intelligence service unavailable: {e}")
        
        # 2. Call Meta Service for historical analysis
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                meta_response = await client.post(
                    f"{SERVICES['meta']}/api/predict",
                    json={
                        "asset": asset,
                        "prediction_type": prediction_type,
                        "confidence": confidence
                    }
                )
                if meta_response.status_code == 200:
                    responses.append({"source": "meta", "data": meta_response.json()})
        except Exception as e:
            logger.warning(f"Meta service unavailable: {e}")
        
        # 3. Call Dashboard for portfolio context
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                dash_response = await client.post(
                    f"{SERVICES['dashboard']}/api/predict",
                    json={"asset": asset, "confidence": confidence}
                )
                if dash_response.status_code == 200:
                    responses.append({"source": "dashboard", "data": dash_response.json()})
        except Exception as e:
            logger.warning(f"Dashboard service unavailable: {e}")
        
        return {
            "success": True,
            "prediction_id": pred_id,
            "asset": asset,
            "asset_type": asset_type,
            "prediction_type": prediction_type,
            "timeframe": timeframe,
            "confidence": confidence,
            "sources": len(responses),
            "responses": responses,
            "timestamp": datetime.now().isoformat(),
            "compliance": "verified"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predict error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ===== UNIFIED /crawl ENDPOINT =====

@app.post("/crawl")
async def unified_crawl(
    request: Request,
    url: str,
    depth: int = 1,
    max_pages: int = 100,
    filters: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = Header(None)
):
    """
    Unified crawl endpoint
    Web crawling and scraping across all sources
    
    Args:
        url: URL to crawl
        depth: Crawl depth (1-5)
        max_pages: Max pages to crawl
        filters: Additional filters (keyword, pattern, etc.)
        user_id: Optional user identifier for audit
    """
    try:
        # Compliance check
        violation = await validate_request_middleware(
            "google",
            "crawl",
            {"url": url, "depth": depth},
            dict(request.headers),
            user_id
        )
        if violation:
            return JSONResponse(status_code=403, content=violation)
        
        # Rate limit check
        if not compliance_validator.check_rate_limit("google", "read"):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Execute crawl
        crawl_results = crawl(
            start_url=url,
            depth=depth,
            max_pages=max_pages,
            filters=filters or {}
        )
        
        # Log crawl job
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs (type, action, payload, status, result)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "crawl",
            "web_scrape",
            json.dumps({"url": url, "depth": depth}),
            "completed",
            json.dumps(crawl_results)
        ))
        conn.commit()
        job_id = cur.lastrowid
        conn.close()
        
        return {
            "success": True,
            "job_id": job_id,
            "url": url,
            "depth": depth,
            "pages_crawled": len(crawl_results.get("pages", [])),
            "data": crawl_results,
            "timestamp": datetime.now().isoformat(),
            "compliance": "verified"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crawl error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ===== UNIFIED /simulate ENDPOINT =====

@app.post("/simulate")
async def unified_simulate(
    request: Request,
    scenario: str,
    asset: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = Header(None)
):
    """
    Unified simulate endpoint
    Backtesting, scenario analysis, market simulations
    
    Args:
        scenario: Scenario name (backtest, monte_carlo, stress_test, etc.)
        asset: Asset to simulate (optional)
        parameters: Simulation parameters
        user_id: Optional user identifier for audit
    """
    try:
        # Compliance check
        violation = await validate_request_middleware(
            "google",
            "simulate",
            {"scenario": scenario, "asset": asset},
            dict(request.headers),
            user_id
        )
        if violation:
            return JSONResponse(status_code=403, content=violation)
        
        # Rate limit check
        if not compliance_validator.check_rate_limit("google", "read"):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Log simulation job
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs (type, action, payload, status)
            VALUES (?, ?, ?, ?)
        """, (
            "simulate",
            scenario,
            json.dumps(parameters or {}),
            "pending"
        ))
        conn.commit()
        job_id = cur.lastrowid
        conn.close()
        
        # Route to Dashboard API for backtesting
        responses = []
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                dash_response = await client.post(
                    f"{SERVICES['dashboard']}/api/simulate",
                    json={
                        "scenario": scenario,
                        "asset": asset,
                        "parameters": parameters or {}
                    }
                )
                if dash_response.status_code == 200:
                    responses.append({"source": "dashboard", "data": dash_response.json()})
        except Exception as e:
            logger.warning(f"Dashboard simulation unavailable: {e}")
        
        # Route to Meta Service
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                meta_response = await client.post(
                    f"{SERVICES['meta']}/api/simulate",
                    json={
                        "scenario": scenario,
                        "parameters": parameters or {}
                    }
                )
                if meta_response.status_code == 200:
                    responses.append({"source": "meta", "data": meta_response.json()})
        except Exception as e:
            logger.warning(f"Meta simulation unavailable: {e}")
        
        return {
            "success": True,
            "job_id": job_id,
            "scenario": scenario,
            "asset": asset,
            "status": "running",
            "responses": responses,
            "timestamp": datetime.now().isoformat(),
            "compliance": "verified"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulate error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ===== PROXY ENDPOINTS FOR OTHER OPERATIONS =====

@app.post("/read/{resource}")
async def proxy_read(resource: str, request: Request):
    """Proxy read operations to appropriate service"""
    body = await request.json()
    
    # Route based on resource
    if resource in ["intelligence", "sources", "categories"]:
        service = "intelligence"
    elif resource in ["portfolio", "bank", "positions"]:
        service = "dashboard"
    elif resource in ["memory", "jobs", "predictions"]:
        service = "meta"
    else:
        service = "meta"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SERVICES[service]}/api/{resource}/read",
                json=body,
                headers={"Authorization": request.headers.get("Authorization", "")}
            )
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/write/{resource}")
async def proxy_write(resource: str, request: Request):
    """Proxy write operations to appropriate service"""
    body = await request.json()
    
    # Route based on resource
    if resource in ["portfolio", "bank"]:
        service = "dashboard"
    elif resource in ["memory", "jobs"]:
        service = "meta"
    else:
        service = "meta"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SERVICES[service]}/api/{resource}/write",
                json=body,
                headers={"Authorization": request.headers.get("Authorization", "")}
            )
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/analyze/{resource}")
async def proxy_analyze(resource: str, request: Request):
    """Proxy analyze operations to appropriate service"""
    body = await request.json()
    
    if resource in ["intelligence", "sources"]:
        service = "intelligence"
    elif resource in ["portfolio", "positions"]:
        service = "dashboard"
    elif resource in ["memory", "predictions"]:
        service = "meta"
    else:
        service = "meta"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SERVICES[service]}/api/{resource}/analyze",
                json=body,
                headers={"Authorization": request.headers.get("Authorization", "")}
            )
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("GATEWAY_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
