import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib

API_KEY = os.environ.get("MCP_API_KEY")
if not API_KEY:
    print("Warning: MCP_API_KEY not set. Requests will be rejected.")

app = FastAPI()

# Serve the .well-known static files from the repository when running in the container.
root_dir = pathlib.Path(__file__).parent.resolve()
well_known_dir = root_dir / ".well-known"
if well_known_dir.exists():
    app.mount("/ .well-known", StaticFiles(directory=str(well_known_dir)), name="well-known")


# Attempt to import the `mcp` package; if it's not available (e.g., local dev without
# installing requirements), provide a small fallback so the adapter can still be
# inspected without raising ImportError immediately.
Server = None
TextContent = None
_server_impl = None

try:
    from mcp.server import Server as MCPServer
    from mcp.types import TextContent as MCPTextContent

    Server = MCPServer
    TextContent = MCPTextContent

    _server_impl = Server(
        name="mcp",
        version="1.0.0",
        capabilities={"tools": {}},
    )

    @_server_impl.tool(name="ping", description="Ping test")
    async def ping():
        return [TextContent(type="text", text="pong")]

    async def _invoke_tool_real(tool, args):
        # Prefer a direct invoke API if available on the server object.
        if hasattr(_server_impl, "invoke_tool"):
            return await _server_impl.invoke_tool(tool, args)
        # Fallback to calling known tools
        if tool == "ping":
            return await ping()
        raise Exception("Tool not available: %s" % tool)

except Exception as e:
    print("Notice: 'mcp' package not available locally; using fallback adapter.", e)

    async def ping():
        return [{"type": "text", "text": "pong"}]

    async def _invoke_tool_real(tool, args):
        if tool == "ping":
            return await ping()
        raise Exception("mcp package not available; tool not found: %s" % tool)


def validate_auth(request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.split(" ", 1)[1]
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/.well-known/openapi.yaml")
async def serve_openapi():
    p = well_known_dir / "openapi.yaml"
    if p.exists():
        return FileResponse(str(p), media_type="text/yaml")
    raise HTTPException(status_code=404, detail="openapi.yaml not found")


@app.get("/.well-known/ai-plugin.json")
async def serve_plugin():
    p = well_known_dir / "ai-plugin.json"
    if p.exists():
        return FileResponse(str(p), media_type="application/json")
    raise HTTPException(status_code=404, detail="ai-plugin.json not found")


@app.get("/.well-known/mcp.json")
async def serve_mcp_json():
    p = root_dir / "mcp.json"
    if p.exists():
        return FileResponse(str(p), media_type="application/json")
    raise HTTPException(status_code=404, detail="mcp.json not found")


@app.get("/logo.png")
async def serve_logo():
    p = root_dir / "logo.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    raise HTTPException(status_code=404, detail="logo.png not found")


@app.post("/run")
async def run_tool(request: Request):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server not configured with MCP_API_KEY")
    validate_auth(request)
    body = await request.json()
    tool = body.get("tool")
    args = body.get("args", {})
    if not tool:
        raise HTTPException(status_code=400, detail="Missing 'tool' field")

    try:
        result = await _invoke_tool_real(tool, args)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
