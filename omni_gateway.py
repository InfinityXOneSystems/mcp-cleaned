"""
Omni Gateway - FastAPI wrapper for main_extended.py MCP server
Exposes 59 Omni Hub tools via HTTP + serves Intelligence Cockpit UI
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import sys
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from google.cloud import firestore
from google.api_core.exceptions import GoogleAPIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Omni Hub MCP server (optional - graceful degradation)
sys.path.insert(0, os.path.dirname(__file__))
try:
    from main_extended import server as mcp_server, check_governance
    MCP_AVAILABLE = True
    logger.info("✓ MCP Server loaded successfully")
except Exception as e:
    logger.warning(f"⚠ MCP Server unavailable: {e}")
    MCP_AVAILABLE = False
    # Mock MCP server for graceful degradation
    class MockMCPServer:
        def list_tools(self): return []
        async def call_tool(self, name, args): return [type('obj', (), {'text': json.dumps({"error": "MCP unavailable"})})]
    mcp_server = MockMCPServer()
    def check_governance(tool_name): return {"level": "MEDIUM", "allowed": True, "reason": "Mock", "rate_limited": False}

app = FastAPI(
    title="Infinity XOS Omni Gateway",
    description="Intelligence Cockpit + 59 MCP Tools + Autonomous Prompt System",
    version="3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== CONFIGURATION =====
FRONTEND_SERVICE_URL = os.environ.get(
    "FRONTEND_SERVICE_URL",
    "https://frontend-service-0a277877-896380409704.us-east1.run.app"
)

# Firestore configuration
FIRESTORE_PROJECT = os.environ.get("FIRESTORE_PROJECT")
FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION", "mcp_memory")

# The 110% Protocol (enterprise-grade, abbreviated)
PROTOCOL_110 = {
    "name": "110% Protocol",
    "version": "1.0",
    "description": "Enterprise-grade FAAN Launch & Rehydrate protocol. Must accept implied YES for safe defaults.",
    "principles": [
        "Always-on observability",
        "Fail-safe defaults (assume yes for non-destructive ops)",
        "Autonomous rehydrate on boot",
        "Store critical runtime memory in Firestore",
        "Governance-first execution",
        "Full launch checklist verification"
    ],
    "checklist": [
        {"id": "c1", "name": "Credentials rotated", "status": "pending"},
        {"id": "c2", "name": "Artifact Registry present (us-east1)", "status": "pending"},
        {"id": "c3", "name": "Cloud Run deployed", "status": "pending"},
        {"id": "c4", "name": "Health endpoints responding", "status": "pending"},
        {"id": "c5", "name": "Frontend <-> Backend routing", "status": "pending"},
        {"id": "c6", "name": "Firestore memory writable", "status": "pending"},
        {"id": "c7", "name": "Autonomous prompt library available", "status": "pending"}
    ]
}

# Firestore client (lazy)
_firestore_client = None
_firestore_available = False

def init_firestore():
    global _firestore_client, _firestore_available
    if _firestore_client:
        return _firestore_client
    try:
        if not FIRESTORE_PROJECT:
            logger.warning("FIRESTORE_PROJECT not set; Firestore disabled")
            _firestore_available = False
            return None
        _firestore_client = firestore.Client(project=FIRESTORE_PROJECT)
        _firestore_available = True
        logger.info("Connected to Firestore project=%s", FIRESTORE_PROJECT)
        return _firestore_client
    except GoogleAPIError as e:
        logger.error(f"Failed to initialize Firestore: {e}")
        _firestore_available = False
        return None
    except Exception as e:
        logger.error(f"Unexpected Firestore init error: {e}")
        _firestore_available = False
        return None

async def load_110_protocol():
    """Write the 110% protocol into Firestore (rehydrate on boot)."""
    client = init_firestore()
    if not client:
        logger.warning("Skipping protocol load; Firestore not available")
        return False
    try:
        doc_ref = client.collection(FIRESTORE_COLLECTION).document("protocol_110")
        doc_ref.set(PROTOCOL_110)
        logger.info("110% Protocol written to Firestore/%s/protocol_110", FIRESTORE_COLLECTION)
        return True
    except Exception as e:
        logger.error(f"Failed to write protocol to Firestore: {e}")
        return False


# Startup event: rehydrate protocol
@app.on_event("startup")
async def on_startup_rehydrate():
    # Initialize Firestore and write protocol document (non-blocking)
    try:
        init_firestore()
        # Fire-and-forget: ensure we don't block startup for long network ops
        asyncio.create_task(load_110_protocol())
    except Exception as e:
        logger.error(f"Startup rehydrate error: {e}")

# ===== COCKPIT UI =====
@app.get("/", response_class=HTMLResponse)
async def serve_cockpit():
    """Serve Intelligence Cockpit UI"""
    try:
        cockpit_path = os.path.join(os.path.dirname(__file__), "cockpit.html")
        with open(cockpit_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Failed to load cockpit: {e}")
        return HTMLResponse(
            content=f"<h1>Cockpit Unavailable</h1><p>{str(e)}</p>",
            status_code=500
        )

# ===== AUTONOMOUS PROMPTS API =====
@app.get("/api/prompts")
async def get_autonomous_prompts():
    """Get autonomous prompt library (L1-L10)"""
    try:
        prompts_path = os.path.join(os.path.dirname(__file__), "AUTONOMOUS_PROMPTS.md")
        with open(prompts_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parse prompts (simple parsing - can be enhanced)
        prompts = []
        lines = content.split("\n")
        current_prompt = None
        
        for line in lines:
            if line.startswith("### "):
                if current_prompt:
                    prompts.append(current_prompt)
                current_prompt = {
                    "name": line.replace("### ", "").strip(),
                    "content": ""
                }
            elif current_prompt and line.strip():
                current_prompt["content"] += line + "\n"
        
        if current_prompt:
            prompts.append(current_prompt)
        
        return JSONResponse(content={
            "success": True,
            "count": len(prompts),
            "prompts": prompts
        })
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/prompts/execute")
async def execute_prompt(request: Request):
    """Execute an autonomous prompt"""
    try:
        data = await request.json()
        prompt_name = data.get("prompt_name")
        context = data.get("context", {})
        
        # Log execution
        logger.info(f"Executing autonomous prompt: {prompt_name}")
        
        # This would integrate with ChatGPT MCP or other execution engine
        return JSONResponse(content={
            "success": True,
            "prompt_name": prompt_name,
            "status": "queued",
            "message": f"Prompt '{prompt_name}' queued for execution"
        })
    except Exception as e:
        logger.error(f"Prompt execution failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ===== MCP TOOLS API =====
@app.get("/api/tools")
async def list_tools():
    """List all available MCP tools"""
    try:
        if not MCP_AVAILABLE:
            return JSONResponse(content={
                "success": False,
                "error": "MCP Server not available",
                "count": 0,
                "tools": []
            })
        
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "governance": check_governance(tool.name)
            }
            for tool in mcp_server.list_tools()
        ]
        
        return JSONResponse(content={
            "success": True,
            "count": len(tools),
            "tools": tools
        })
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@app.post("/api/tools/execute")
async def execute_tool(tool_req: ToolRequest):
    """Execute an MCP tool"""
    try:
        # Check governance
        gov_check = check_governance(tool_req.tool_name)
        if not gov_check["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded or operation blocked",
                    "governance": gov_check
                }
            )
        
        # Execute tool via MCP server
        result = await mcp_server.call_tool(tool_req.tool_name, tool_req.arguments)
        
        return JSONResponse(content={
            "success": True,
            "tool": tool_req.tool_name,
            "result": str(result[0].text) if result else None
        })
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ===== CLI INTEGRATION =====
@app.post("/api/cli/execute")
async def execute_cli_command(request: Request):
    """Execute CLI commands (with governance)"""
    try:
        data = await request.json()
        command = data.get("command")
        
        # Check governance for critical commands
        if any(dangerous in command.lower() for dangerous in ["rm -rf", "del /f", "format", "shutdown"]):
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "Command blocked by governance - critical operation"
                }
            )
        
        # Execute via orchestrator tool
        result = await mcp_server.call_tool("execute", {"command": command})
        
        return JSONResponse(content={
            "success": True,
            "command": command,
            "output": str(result[0].text) if result else None
        })
    except Exception as e:
        logger.error(f"CLI execution failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ===== SYSTEM STATUS =====
@app.get("/api/status")
async def get_system_status():
    """Get system status and metrics"""
    try:
        tools_count = len(mcp_server.list_tools()) if MCP_AVAILABLE else 0
        
        return JSONResponse(content={
            "success": True,
            "status": "operational",
            "components": {
                "omni_hub": "active" if MCP_AVAILABLE else "degraded",
                "mcp_tools": tools_count,
                "cockpit": "online",
                "frontend_service": FRONTEND_SERVICE_URL,
                "autonomous_prompts": "loaded",
                "cli_integration": "enabled"
            },
            "governance": "enforced"
        })
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ===== FRONTEND SERVICE PROXY =====
@app.get("/frontend")
async def frontend_proxy():
    """Proxy Cloud Run frontend service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(FRONTEND_SERVICE_URL, timeout=30.0)
            return HTMLResponse(content=response.text)
    except Exception as e:
        logger.error(f"Frontend proxy failed: {e}")
        return HTMLResponse(
            content=f"<h1>Frontend Service Unavailable</h1><p>{str(e)}</p>",
            status_code=503
        )

@app.get("/frontend/api/{path:path}")
async def frontend_api_proxy(path: str, request: Request):
    """Proxy API requests to frontend service"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{FRONTEND_SERVICE_URL}/api/{path}"
            response = await client.request(
                method=request.method,
                url=url,
                headers=dict(request.headers),
                timeout=30.0
            )
            return JSONResponse(content=response.json())
    except Exception as e:
        logger.error(f"Frontend API proxy failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"error": f"Frontend service error: {str(e)}"}
        )

# ===== HEALTH CHECK =====
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={"status": "healthy", "service": "omni-gateway"})


# ===== 110% Protocol & Launch Checklist Endpoints =====
@app.get("/api/protocol")
async def get_protocol():
    """Return the in-memory 110% protocol and indicate Firestore availability"""
    return JSONResponse(content={
        "success": True,
        "protocol": PROTOCOL_110,
        "firestore": _firestore_available
    })


@app.post("/api/protocol/rehydrate")
async def rehydrate_protocol():
    """Force rehydrate/write protocol to Firestore now"""
    ok = await load_110_protocol()
    if ok:
        return JSONResponse(content={"success": True, "message": "Protocol rehydrated to Firestore"})
    else:
        return JSONResponse(status_code=500, content={"success": False, "error": "Failed to rehydrate protocol"})


@app.get("/api/checklist")
async def get_checklist():
    """Return the launch checklist (from Firestore if available, otherwise in-memory)"""
    client = init_firestore()
    if client:
        try:
            doc = client.collection(FIRESTORE_COLLECTION).document("protocol_110").get()
            if doc.exists:
                data = doc.to_dict()
                checklist = data.get("checklist", PROTOCOL_110["checklist"])
                return JSONResponse(content={"success": True, "checklist": checklist})
        except Exception as e:
            logger.error(f"Failed to read checklist from Firestore: {e}")

    # Fallback to in-memory
    return JSONResponse(content={"success": True, "checklist": PROTOCOL_110["checklist"]})


class ChecklistUpdate(BaseModel):
    id: str
    status: str


@app.post("/api/checklist/update")
async def update_checklist(item: ChecklistUpdate):
    """Update a checklist item status and persist to Firestore if available"""
    # Update in-memory
    found = False
    for it in PROTOCOL_110["checklist"]:
        if it["id"] == item.id:
            it["status"] = item.status
            found = True
            break

    if not found:
        return JSONResponse(status_code=404, content={"success": False, "error": "Checklist item not found"})

    client = init_firestore()
    if client:
        try:
            doc_ref = client.collection(FIRESTORE_COLLECTION).document("protocol_110")
            doc_ref.set(PROTOCOL_110, merge=True)
            return JSONResponse(content={"success": True, "message": "Checklist updated and persisted"})
        except Exception as e:
            logger.error(f"Failed to persist checklist update: {e}")
            return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

    return JSONResponse(content={"success": True, "message": "Checklist updated (in-memory only)"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
