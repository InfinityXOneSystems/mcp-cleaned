"""
Intelligence Dashboard API - Industry Browser & Scheduler
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "mcp_memory.db"
DEFAULT_PORT = int(os.environ.get("INTELLIGENCE_PORT", "8002"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "intelligence_api"}


@app.get("/")
async def root():
    with open("intelligence_browser.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/intelligence_browser.html")
async def browser():
    with open("intelligence_browser.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


def get_intelligence_sources():
    """Get all categorized intelligence sources"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, key, value 
        FROM memory 
        WHERE value LIKE '%url%'
        LIMIT 1500
    """
    )

    records = cursor.fetchall()
    conn.close()

    categories = {}

    for record_id, key, value in records:
        try:
            data = json.loads(value) if value else {}
            url = data.get("url", "")

            if not url:
                continue

            # Categorize
            category = None
            subcategory = None

            if "sba.gov" in url:
                category, subcategory = "Business Loans", "SBA"
            elif "ucc" in url.lower():
                category, subcategory = "Business Loans", "UCC Filings"
            elif "chamber" in url.lower():
                category, subcategory = "Business Loans", "Chambers of Commerce"
            elif "business" in url.lower() and "license" in url.lower():
                category, subcategory = "Business Loans", "Business Licenses"
            elif "gofundme" in url.lower():
                category, subcategory = "Crowdfunding", "GoFundMe"
            elif "biggerpockets" in url.lower():
                category, subcategory = "Social Sentiment", "BiggerPockets"
            elif "reddit" in url.lower():
                category, subcategory = "Social Sentiment", "Reddit"
            elif "twitter" in url.lower():
                category, subcategory = "Social Sentiment", "Twitter"
            elif "foreclosure" in url.lower():
                category, subcategory = "Real Estate", "Foreclosures"
            elif "permit" in url.lower():
                category, subcategory = "Real Estate", "Building Permits"
            elif "property" in url.lower() or "real" in url.lower():
                category, subcategory = "Real Estate", "Property Records"
            elif "court" in url.lower() or "filing" in url.lower():
                category, subcategory = "County Records", "Court Filings"
            elif "lien" in url.lower():
                category, subcategory = "County Records", "Liens"
            elif "news" in url.lower() or "journal" in url.lower():
                category, subcategory = "News", "Local Business News"

            if category and subcategory:
                if category not in categories:
                    categories[category] = {}
                if subcategory not in categories[category]:
                    categories[category][subcategory] = []

                categories[category][subcategory].append(
                    {"id": record_id, "url": url, "key": key, "data": data}
                )
        except:
            pass

    return categories


@app.get("/api/intelligence/categories")
async def get_categories():
    """Get all categories and subcategories with counts"""
    sources = get_intelligence_sources()
    result = {}

    for category, subcats in sources.items():
        result[category] = {subcat: len(urls) for subcat, urls in subcats.items()}

    return result


@app.get("/api/intelligence/sources")
async def get_sources(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
):
    """Get intelligence sources filtered by category, subcategory, or search term"""
    sources = get_intelligence_sources()

    if category and category in sources:
        if subcategory and subcategory in sources[category]:
            results = sources[category][subcategory]
        else:
            # All subcategories in this category
            results = []
            for subcat_sources in sources[category].values():
                results.extend(subcat_sources)
    else:
        # All sources
        results = []
        for cat_sources in sources.values():
            for subcat_sources in cat_sources.values():
                results.extend(subcat_sources)

    # Apply search filter
    if search:
        search_lower = search.lower()
        results = [
            r
            for r in results
            if search_lower in r["url"].lower()
            or search_lower in r.get("key", "").lower()
        ]

    return {
        "count": len(results),
        "sources": results[:100],  # Limit to 100 for performance
    }


@app.get("/api/intelligence/preview/{source_id}")
async def get_source_preview(source_id: int):
    """Get full data for a specific source"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT key, value FROM memory WHERE id = ?", (source_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Source not found")

    key, value = result
    data = json.loads(value) if value else {}

    return {"id": source_id, "key": key, "data": data}


# ===== UNIFIED ENDPOINTS FOR GATEWAY COMPATIBILITY =====


@app.post("/api/predict")
async def predict(asset: str, timeframe: str = "24h"):
    """Predict endpoint - intelligence-based sentiment analysis"""
    sources = get_intelligence_sources()

    # Count sources related to asset
    relevant_sources = 0
    for category, subcats in sources.items():
        for subcat, sources_list in subcats.items():
            for source in sources_list:
                if asset.lower() in source.get("url", "").lower():
                    relevant_sources += 1

    return {
        "success": True,
        "asset": asset,
        "timeframe": timeframe,
        "relevant_sources": relevant_sources,
        "source": "intelligence",
    }


@app.post("/api/crawl")
async def crawl(url: str, depth: int = 1):
    """Crawl endpoint - intelligence data gathering"""
    return {
        "success": True,
        "url": url,
        "depth": depth,
        "status": "queued",
        "source": "intelligence",
    }


@app.post("/api/simulate")
async def simulate(scenario: str, parameters: Optional[dict] = None):
    """Simulate endpoint - sentiment scenario testing"""
    return {
        "success": True,
        "scenario": scenario,
        "parameters": parameters or {},
        "status": "queued",
        "source": "intelligence",
    }


@app.get("/api/read/{resource}")
async def read_resource(resource: str):
    """Unified read endpoint"""
    if resource == "sources":
        return await get_sources()
    elif resource == "categories":
        return await get_categories()
    else:
        raise HTTPException(status_code=404, detail=f"Resource {resource} not found")


@app.post("/api/write/{resource}")
async def write_resource(resource: str, payload: dict):
    """Unified write endpoint"""
    raise HTTPException(status_code=405, detail="Intelligence API is read-only")


@app.post("/api/analyze/{resource}")
async def analyze_resource(resource: str, payload: dict):
    """Unified analyze endpoint"""
    if resource == "sources":
        sources = get_intelligence_sources()
        return {
            "resource": resource,
            "analysis": {
                "total_categories": len(sources),
                "total_sources": sum(
                    len(s) for c in sources.values() for s in c.values()
                ),
            },
        }
    else:
        raise HTTPException(status_code=404, detail=f"Resource {resource} not found")


if __name__ == "__main__":
    import socket

    import uvicorn

    def can_bind(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
            return True
        except Exception:
            return False

    port = DEFAULT_PORT
    if not can_bind(port):
        # Try fallback ports
        for candidate in (8012, 8082):
            if can_bind(candidate):
                port = candidate
                break
        else:
            # Last resort: random OS-assigned port (not ideal for SPA)
            port = 0

    uvicorn.run(app, host="0.0.0.0", port=port)
