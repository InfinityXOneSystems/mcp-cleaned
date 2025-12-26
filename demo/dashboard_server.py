import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import httpx

app = FastAPI(title="MCP Demo Dashboard Server")

# Serve the static dashboard file
DASH_HTML = os.path.join(os.path.dirname(__file__), "..", "webview", "dashboard.html")
DASH_HTML = os.path.normpath(DASH_HTML)

@app.get("/", include_in_schema=False)
async def root():
    if not os.path.exists(DASH_HTML):
        raise HTTPException(status_code=404, detail=f"Dashboard not found at {DASH_HTML}")
    return FileResponse(DASH_HTML, media_type="text/html")

# Default backend (can be overridden by environment or request)
BACKEND_DEFAULT = os.environ.get("MCP_BACKEND_URL", "http://localhost:8000")

@app.get("/api/proxy/health")
async def proxy_health(base_url: str = None):
    target = (base_url or BACKEND_DEFAULT).rstrip("/") + "/health"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(target)
            r.raise_for_status()
            if "application/json" in (r.headers.get("content-type") or ""):
                return JSONResponse(r.json())
            return JSONResponse({"status": r.text})
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Request error: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))

@app.post("/api/proxy/predict")
async def proxy_predict(request: Request):
    body = await request.json()
    base_url = body.get("base_url") or BACKEND_DEFAULT
    payload = body.get("payload", {})
    target = base_url.rstrip("/") + "/predict"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(target, json=payload)
            if "application/json" in (r.headers.get("content-type") or ""):
                return JSONResponse(r.json())
            return JSONResponse({"status": r.status_code, "text": r.text})
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Request error: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("demo.dashboard_server:app", host="0.0.0.0", port=9000, reload=False)
