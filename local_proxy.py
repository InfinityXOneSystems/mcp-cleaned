import os

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve static landing pages from landing_pages
static_dir = os.path.join(os.path.dirname(__file__), "landing_pages")
app.mount(
    "/static", StaticFiles(directory=os.path.join(static_dir, "static")), name="static"
)

# Configurable mapping for hostnames -> local routes
MAPPED_HOSTS = {
    "infinityxai.com": "/index.html",
    "infinityxonesystems.com": "/index.html",
}

# Admin backend to proxy to local gateway
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000")


@app.middleware("http")
async def host_router(request: Request, call_next):
    host = request.headers.get("host", "")
    path = request.url.path
    # If path starts with /admin or /api, proxy to gateway
    if (
        path.startswith("/admin")
        or path.startswith("/api")
        or path.startswith("/sheets")
        or path.startswith("/calendar")
    ):
        async with httpx.AsyncClient() as client:
            target = GATEWAY_URL + path
            try:
                if request.method in ("POST", "PUT", "PATCH"):
                    body = await request.body()
                    resp = await client.request(
                        request.method, target, content=body, headers=request.headers
                    )
                else:
                    resp = await client.request(
                        request.method,
                        target,
                        params=dict(request.query_params),
                        headers=request.headers,
                    )
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers=resp.headers,
                )
            except Exception as e:
                return Response(content=f"Gateway proxy error: {e}", status_code=502)

    # If host matches mapped hostnames, serve landing page
    hostname = host.split(":")[0]
    if hostname in MAPPED_HOSTS:
        target_file = os.path.join(static_dir, MAPPED_HOSTS[hostname].lstrip("/"))
        if os.path.exists(target_file):
            return FileResponse(target_file, media_type="text/html")
        else:
            return HTMLResponse("<h1>Landing page not found</h1>", status_code=404)

    # Default: if file path exists in landing_pages, serve it
    candidate = os.path.join(static_dir, path.lstrip("/"))
    if os.path.exists(candidate) and os.path.isfile(candidate):
        return FileResponse(candidate)

    # Fallback to root landing page
    root = os.path.join(static_dir, "index.html")
    return FileResponse(root)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("local_proxy:app", host="0.0.0.0", port=8080, reload=False)
