"""Clean MCP HTTP Adapter (single, concise implementation)

This module provides a FastAPI `router` at `/mcp` with the following
"""Minimal MCP HTTP Adapter (clean)

This module exports `router` (FastAPI APIRouter) mounted at /mcp. It keeps
imports lightweight and reads the tool registry lazily from main_extended.
"""

from typing import Dict, Any, List, Optional
import os
import json
import logging
import hashlib
from datetime import datetime
import asyncio

from fastapi import APIRouter, Query, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    request_id: Optional[str] = None


SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


def _load_tools_from_main() -> List[Dict[str, Any]]:
    try:
        from main_extended import TOOLS, check_governance
        out = []
        for t in TOOLS:
            out.append({
                "name": t.name,
                "description": getattr(t, "description", ""),
                "inputSchema": getattr(t, "inputSchema", {}),
                "governance": check_governance(t.name),
            })
        return out
    except Exception:
        return []


def _build_registry() -> Dict[str, Dict[str, Any]]:
    tools = _load_tools_from_main()
    reg: Dict[str, Dict[str, Any]] = {}
    for t in tools:
        name = t.get("name")
        schema = t.get("inputSchema") or {}
        params = []
        for k, v in (schema.get("properties") or {}).items():
            params.append({
                "name": k,
                "type": v.get("type", "string"),
                "description": v.get("description", ""),
                "required": k in (schema.get("required") or []),
            })
        gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
        reg[name] = {
            "name": name,
            "description": t.get("description", ""),
            "parameters": params,
            "rate_limit_level": gov.get("level", "MEDIUM"),
            "approval_required": gov.get("level") == "CRITICAL",
        }
    return reg


REGISTRY = _build_registry()

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/health")
async def health():
    return {"status": "healthy", "mcp_server_available": bool(REGISTRY), "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get("/tools")

"""MCP HTTP Adapter - clean single-file implementation.

This module exposes a FastAPI `router` that can be mounted under the
`/mcp` prefix. It lazily reads `main_extended.TOOLS` to build a small
registry, enforces SAFE_MODE via an `X-MCP-KEY` header, supports dry-run,
persists approval requests for CRITICAL operations, and exposes a
minimal OpenAPI spec annotated with x-mcp-attach-ready.
"""

from typing import Optional, Dict, Any, List
import os
import json
import logging
from datetime import datetime
import asyncio

from fastapi import APIRouter, Query, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    _approved: Optional[bool] = False
    background: Optional[bool] = False
    request_id: Optional[str] = None


class ExecuteResponse(BaseModel):
    success: bool
    request_id: str
    tool_name: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    governance_level: Optional[str] = None


SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


def _load_tools_from_main() -> List[Dict[str, Any]]:
    # Lazy import to avoid heavy startup costs at module import time
    try:
        from main_extended import TOOLS, check_governance
        out = []
        for t in TOOLS:
            out.append({
                "name": getattr(t, "name", None),
                "description": getattr(t, "description", ""),
                "inputSchema": getattr(t, "inputSchema", {}),
                "governance": check_governance(getattr(t, "name", "")),
            })
        return out
    except Exception:
        return []


def _build_registry() -> Dict[str, Dict[str, Any]]:
    tools = _load_tools_from_main()
    reg: Dict[str, Dict[str, Any]] = {}
    for t in tools:
        name = t.get("name")
        if not name:
            continue
        schema = t.get("inputSchema") or {}
        params = []
        for k, v in (schema.get("properties") or {}).items():
            params.append({
                "name": k,
                "type": v.get("type", "string"),
                "description": v.get("description", ""),
                "required": k in (schema.get("required") or []),
            })
        gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
        reg[name] = {
            "name": name,
            "description": t.get("description", ""),
            "parameters": params,
            "rate_limit_level": gov.get("level", "MEDIUM"),
            "approval_required": gov.get("level") == "CRITICAL",
        }
    return reg


REGISTRY = _build_registry()

router = APIRouter(prefix="/mcp", tags=["mcp"])


def _validate_key(x_mcp_key: Optional[str], read_only: bool = False):
    if not SAFE_MODE:
        return True
    key = x_mcp_key or os.environ.get("MCP_API_KEY")
    if not key or key != MCP_API_KEY:
        if read_only:
            # allow read-only operations without key when explicitly requested
            return False
        raise HTTPException(status_code=401, detail="Missing or invalid X-MCP-KEY header")
    return True


async def _invoke_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    try:
        from main_extended import server

        fn = getattr(server, "call_tool", None)
        if fn is None:
            raise RuntimeError("server.call_tool is not available in main_extended")

        if asyncio.iscoroutinefunction(fn):
            return await fn(tool_name, arguments)
        else:
            return await asyncio.to_thread(fn, tool_name, arguments)
    except Exception:
        logger.exception("error invoking tool %s", tool_name)
        raise


def _persist_approval_request(tool_name: str, arguments: Dict[str, Any], metadata: Dict[str, Any]):
    try:
        from memory import helpers as mem_helpers

        doc = {
            "session_hash": hashlib.sha256(f"{tool_name}{json.dumps(arguments, sort_keys=True)}".encode()).hexdigest(),
            "type": "approval_request",
            "content": {"tool_name": tool_name, "arguments": arguments, "metadata": metadata},
            "confidence": 1.0,
            "sources": [],
            "prompt_hash": None,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        # write_local_memory may accept different args; attempt best-effort call
        if hasattr(mem_helpers, "write_local_memory"):
            try:
                mem_helpers.write_local_memory(doc)
            except TypeError:
                # fallback: try a more generic call
                mem_helpers.write_local_memory(doc.get("session_hash"), doc)
    except Exception:
        logger.exception("failed to persist approval request for %s", tool_name)


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0",
        "protocol_version": "2024-11",
        "mcp_server_available": bool(REGISTRY),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/tools")
async def list_tools():
    return JSONResponse(content={"tools": list(REGISTRY.values())})


@router.post("/execute")
async def execute(req: ExecuteRequest, x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    # Validate request
    tool = REGISTRY.get(req.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"tool not found: {req.tool_name}")

    # SAFE_MODE enforcement
    try:
        _validate_key(x_mcp_key, read_only=bool(x_mcp_readonly))
    except HTTPException:
        # allow read-only access to tools marked as read-only if header indicates
        if not x_mcp_readonly:
            raise

    gov_level = tool.get("rate_limit_level")
    approval_required = tool.get("approval_required", False)

    # Dry-run: return parameter schema and governance info without executing
    if req.dry_run:
        return JSONResponse(content={
            "success": True,
            "request_id": req.request_id or "dryrun",
            "tool_name": req.tool_name,
            "result": {"parameters": tool.get("parameters", []), "governance_level": gov_level, "approval_required": approval_required},
        })

    # Approval flow for critical ops
    if approval_required and not getattr(req, "_approved", False):
        # persist approval request and return a response indicating approval required
        _persist_approval_request(req.tool_name, req.arguments, {"governance_level": gov_level})
        return JSONResponse(status_code=202, content={
            "success": False,
            "request_id": req.request_id or "approval_required",
            "tool_name": req.tool_name,
            "error": "approval_required",
            "governance_level": gov_level,
        })

    # Background execution support
    if req.background:
        async def _bg():
            try:
                await _invoke_tool(req.tool_name, req.arguments)
            except Exception:
                logger.exception("background execution failed for %s", req.tool_name)

        asyncio.create_task(_bg())
        return JSONResponse(status_code=202, content={"success": True, "request_id": req.request_id or "background", "tool_name": req.tool_name})

    # Execute synchronously and return result
    start = datetime.utcnow()
    try:
        result = await _invoke_tool(req.tool_name, req.arguments)
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000.0
        return JSONResponse(content={
            "success": True,
            "request_id": req.request_id or "ok",
            "tool_name": req.tool_name,
            "result": result,
            "execution_time_ms": elapsed,
            "governance_level": gov_level,
        })
    except Exception as e:
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000.0
        logger.exception("tool execute error")
        return JSONResponse(status_code=500, content={"success": False, "request_id": req.request_id or "error", "tool_name": req.tool_name, "error": str(e), "execution_time_ms": elapsed, "governance_level": gov_level})


@router.post("/execute/{tool_name}")
async def execute_named(tool_name: str, arguments: Dict[str, Any], dry_run: bool = Query(False), x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    req = ExecuteRequest(tool_name=tool_name, arguments=arguments, dry_run=dry_run)
    return await execute(req, x_mcp_key=x_mcp_key, x_mcp_readonly=x_mcp_readonly)


@router.get("/openapi")
async def openapi(base_url: Optional[str] = Query("http://localhost:8000")):
    paths = {}
    for name, t in REGISTRY.items():
        params = {p['name']: {"type": p.get('type', 'string'), "description": p.get('description', '')} for p in t.get('parameters', [])}
        paths[f"/mcp/execute/{name}"] = {
            "post": {
                "summary": f"Execute {name}",
                "description": t.get('description', ''),
                "operationId": f"execute_{name}",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object", "properties": params}}}},
                "responses": {"200": {"description": "OK"}}
            }
        }
    spec = {"openapi": "3.0.0", "info": {"title": "Infinity XOS MCP Adapter", "version": "1.0"}, "servers": [{"url": base_url}], "paths": paths}
    spec["x-mcp-attach-ready"] = True
    return JSONResponse(content=spec)

                "required": k in (schema.get("required") or []),
            })
        gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
        reg[name] = {
            "name": name,
            "description": t.get("description", ""),
            "parameters": params,
            "rate_limit_level": gov.get("level", "MEDIUM"),
            "approval_required": gov.get("level") == "CRITICAL",
        }
    return reg


REGISTRY = _build_registry()

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0",
        "protocol_version": "2024-11",
        "mcp_server_available": bool(REGISTRY),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/tools")
async def tools():
    return {"count": len(REGISTRY), "tools": list(REGISTRY.values())}


def _validate_key(x_mcp_key: Optional[str], read_only: bool) -> bool:
    if SAFE_MODE:
        return x_mcp_key == MCP_API_KEY or read_only
    return True


async def _call_tool_background(tool_name: str, arguments: Dict[str, Any]):
    # This helper runs the tool in the background using asyncio.create_task
    try:
        from main_extended import server as mcp_server

        if not hasattr(mcp_server, "call_tool"):
            raise RuntimeError("MCP server missing call_tool")

        # call_tool may be async or sync; handle both
        coro = mcp_server.call_tool(tool_name, arguments)
        if asyncio.iscoroutine(coro):
            return await coro
        else:
            # run sync function in threadpool
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: coro)
    except Exception as e:
        logger.exception("background call_tool error")
        raise


@router.post("/execute")
async def execute(req: ExecuteRequest, x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    start = datetime.utcnow()
    rid = req.request_id or hashlib.sha256(f"{req.tool_name}{start.isoformat()}".encode()).hexdigest()[:16]
    if req.tool_name not in REGISTRY:
        raise HTTPException(status_code=400, detail="Unknown tool")
    tool = REGISTRY[req.tool_name]
    if not _validate_key(x_mcp_key, bool(x_mcp_readonly)):
        raise HTTPException(status_code=401, detail="Unauthorized: X-MCP-KEY invalid or missing")

    # Approval persistence for critical tools
    if tool.get("approval_required") and not bool(req.arguments.get("_approved", False)):
        try:
            from memory.helpers import write_local_memory

            mem = {
                "type": "tool_request",
                "tool_name": req.tool_name,
                "arguments": req.arguments,
                "requires_approval": True,
                "approval_status": "pending",
                "requested_by": x_mcp_key or "anonymous",
            }
            mem_id = write_local_memory(mem)
        except Exception:
            mem_id = None
        return JSONResponse(status_code=200, content={
            "success": False,
            "request_id": rid,
            "tool_name": req.tool_name,
            "result": {"approval_required": True, "memory_id": mem_id},
            "error": "approval_required",
            "execution_time_ms": 0,
            "governance_level": tool.get("rate_limit_level"),
        })

    if req.dry_run:
        return JSONResponse(status_code=200, content={
            "success": True,
            "request_id": rid,
            "tool_name": req.tool_name,
            "result": {"dry_run": True, "parameters_provided": list(req.arguments.keys())},
            "execution_time_ms": 0,
            "governance_level": tool.get("rate_limit_level"),
        })

    # Execute the tool but run in background if long-running is expected. We still
    # await the result here to return it synchronously; background execution is
    # supported by returning quickly and scheduling a task when callers want it.
    try:
        # If caller included _background=True in arguments, schedule and return
        if bool(req.arguments.get("_background", False)):
            # schedule without awaiting, return immediate ACK with request id
            asyncio.create_task(_call_tool_background(req.tool_name, req.arguments))
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            return JSONResponse(status_code=202, content={
                "success": True,
                "request_id": rid,
                "tool_name": req.tool_name,
                "result": {"scheduled": True},
                "execution_time_ms": elapsed,
                "governance_level": tool.get("rate_limit_level"),
            })

        result = await _call_tool_background(req.tool_name, req.arguments)
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        # attempt to decode common wrappers
        try:
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], "text"):
                payload = json.loads(result[0].text)
            else:
                payload = result
        except Exception:
            payload = result
        return JSONResponse(status_code=200, content={
            "success": True,
            "request_id": rid,
            "tool_name": req.tool_name,
            "result": payload,
            "execution_time_ms": elapsed,
            "governance_level": tool.get("rate_limit_level"),
        })
    except Exception as e:
        logger.exception("tool execute error")
        return JSONResponse(status_code=500, content={
            "success": False,
            "request_id": rid,
            "tool_name": req.tool_name,
            "error": str(e),
            "execution_time_ms": 0,
            "governance_level": tool.get("rate_limit_level"),
        })


@router.post("/execute/{tool_name}")
async def execute_named(tool_name: str, arguments: Dict[str, Any], dry_run: bool = Query(False), x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    req = ExecuteRequest(tool_name=tool_name, arguments=arguments, dry_run=dry_run)
    return await execute(req, x_mcp_key=x_mcp_key, x_mcp_readonly=x_mcp_readonly)


@router.get("/openapi")
async def openapi(base_url: Optional[str] = Query("http://localhost:8000")) -> Dict[str, Any]:
    # Minimal OpenAPI generator suitable for attachment; stateless and self-contained
    paths: Dict[str, Any] = {}
    for name, t in REGISTRY.items():
        schema_props = {p['name']: {"type": p.get('type', 'string'), "description": p.get('description', '')} for p in t.get('parameters', [])}
        paths[f"/mcp/execute/{name}"] = {
            "post": {
                "summary": t.get('description', '') or f"Execute {name}",
                "responses": {"200": {"description": "OK"}},
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": schema_props,
                            }
                        }
                    }
                }
            }
        }

    openapi_spec = {
        "openapi": "3.0.1",
        "info": {"title": "MCP HTTP Adapter", "version": "1.0", "x-mcp-attach-ready": True},
        "servers": [{"url": base_url}],
        "paths": paths,
    }
    return openapi_spec

    execution_time_ms: float = 0
    governance_level: Optional[str] = None


SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


def _load_tools_from_main() -> List[Dict[str, Any]]:
    try:
        from main_extended import TOOLS, check_governance
        out = []
        for t in TOOLS:
            out.append({
                "name": t.name,
                "description": getattr(t, "description", ""),
                "inputSchema": getattr(t, "inputSchema", {}),
                "governance": check_governance(t.name),
            })
        return out
    except Exception:
        return []


def _build_registry() -> Dict[str, Dict[str, Any]]:
    tools = _load_tools_from_main()
    reg: Dict[str, Dict[str, Any]] = {}
    for t in tools:
        name = t.get("name")
        schema = t.get("inputSchema") or {}
        params = []
        for k, v in (schema.get("properties") or {}).items():
            params.append({
                "name": k,
                "type": v.get("type", "string"),
                "description": v.get("description", ""),
                "required": k in (schema.get("required") or []),
            })
        gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
        reg[name] = {
            "name": name,
            "description": t.get("description", ""),
            "parameters": params,
            "rate_limit_level": gov.get("level", "MEDIUM"),
            "approval_required": gov.get("level") == "CRITICAL",
        }
    return reg


REGISTRY = _build_registry()

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0",
        "protocol_version": "2024-11",
        "mcp_server_available": bool(REGISTRY),
        "firestore_available": False,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/tools")
async def tools():
    return {"count": len(REGISTRY), "tools": list(REGISTRY.values())}


def _validate_key(x_mcp_key: Optional[str], read_only: bool) -> bool:
    if SAFE_MODE:
        return x_mcp_key == MCP_API_KEY or read_only
    return True


@router.post("/execute")
async def execute(req: ExecuteRequest, x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    start = datetime.utcnow()
    rid = req.request_id or hashlib.sha256(f"{req.tool_name}{start.isoformat()}".encode()).hexdigest()[:16]
    if req.tool_name not in REGISTRY:
        raise HTTPException(status_code=400, detail="Unknown tool")
    tool = REGISTRY[req.tool_name]
    if not _validate_key(x_mcp_key, bool(x_mcp_readonly)):
        raise HTTPException(status_code=401, detail="Unauthorized: X-MCP-KEY invalid or missing")
    if tool.get("approval_required") and not bool(req.arguments.get("_approved", False)):
        try:
            from memory.helpers import write_local_memory
            mem = {"type": "tool_request", "tool_name": req.tool_name, "arguments": req.arguments, "requires_approval": True, "approval_status": "pending", "requested_by": x_mcp_key or "anonymous"}
            mem_id = write_local_memory(mem)
        except Exception:
            mem_id = None
        return JSONResponse(status_code=200, content={"success": False, "request_id": rid, "tool_name": req.tool_name, "result": {"approval_required": True, "memory_id": mem_id}, "error": "approval_required", "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})
    if req.dry_run:
        return JSONResponse(status_code=200, content={"success": True, "request_id": rid, "tool_name": req.tool_name, "result": {"dry_run": True, "parameters_provided": list(req.arguments.keys())}, "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})
    try:
        from main_extended import server as mcp_server
        if not hasattr(mcp_server, 'call_tool'):
            raise RuntimeError("MCP server missing call_tool")
        result = await mcp_server.call_tool(req.tool_name, req.arguments)
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        try:
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                payload = json.loads(result[0].text)
            else:
                payload = result
        except Exception:
            payload = result
        return JSONResponse(status_code=200, content={"success": True, "request_id": rid, "tool_name": req.tool_name, "result": payload, "execution_time_ms": elapsed, "governance_level": tool.get("rate_limit_level")})
    except Exception as e:
        logger.exception("tool execute error")
        return JSONResponse(status_code=500, content={"success": False, "request_id": rid, "tool_name": req.tool_name, "error": str(e), "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})


@router.post("/execute/{tool_name}")
async def execute_named(tool_name: str, arguments: Dict[str, Any], dry_run: bool = Query(False), x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    req = ExecuteRequest(tool_name=tool_name, arguments=arguments, dry_run=dry_run)
    return await execute(req, x_mcp_key=x_mcp_key, x_mcp_readonly=x_mcp_readonly)


@router.get("/openapi")
async def openapi(base_url: Optional[str] = Query("http://localhost:8000")):
    paths = {}
    for name, t in REGISTRY.items():
        params = {p['name']: {"type": p.get('type', 'string'), "description": p.get('description', '')} for p in t.get('parameters', [])}
        paths[f"/mcp/execute/{name}"] = {
            "post": {
                "summary": f"Execute {name}",
                "description": t.get('description', ''),
                "operationId": f"execute_{name}",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object", "properties": params}}}},
                "responses": {"200": {"description": "OK"}}
            }
        }
    spec = {"openapi": "3.0.0", "info": {"title": "Infinity XOS MCP Adapter", "version": "1.0"}, "servers": [{"url": base_url}], "paths": paths}
    spec["x-mcp-attach-ready"] = True
    return JSONResponse(content=spec)
"""MCP HTTP Adapter — minimal clean implementation

Exports `router` (FastAPI APIRouter) under prefix `/mcp` with:
- GET /mcp/health
- GET /mcp/tools
- POST /mcp/execute
- POST /mcp/execute/{tool_name}
- GET /mcp/openapi

This module is intentionally small and avoids complex runtime
dependencies at import time. It reads `main_extended.TOOLS` lazily.
"""
from fastapi import APIRouter, Query, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import os
import json
import logging
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    request_id: Optional[str] = None


class ExecuteResponse(BaseModel):
    success: bool
    request_id: str
    tool_name: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    governance_level: Optional[str] = None


SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


def _load_tools_from_main() -> List[Dict[str, Any]]:
    try:
        from main_extended import TOOLS, check_governance
        out = []
        for t in TOOLS:
            out.append({
                "name": t.name,
                "description": getattr(t, "description", ""),
                "inputSchema": getattr(t, "inputSchema", {}),
                "governance": check_governance(t.name),
            })
        return out
    except Exception:
        return []


def _build_registry() -> Dict[str, Dict[str, Any]]:
    tools = _load_tools_from_main()
    reg: Dict[str, Dict[str, Any]] = {}
    for t in tools:
        name = t.get("name")
        schema = t.get("inputSchema") or {}
        params = []
        for k, v in (schema.get("properties") or {}).items():
            params.append({
                "name": k,
                "type": v.get("type", "string"),
                "description": v.get("description", ""),
                "required": k in (schema.get("required") or []),
            })
        gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
        reg[name] = {
            "name": name,
            "description": t.get("description", ""),
            "parameters": params,
            "rate_limit_level": gov.get("level", "MEDIUM"),
            "approval_required": gov.get("level") == "CRITICAL",
        }
    return reg


REGISTRY = _build_registry()

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        """MCP HTTP Adapter — final clean minimal implementation

        This file is intentionally minimal and safe to import. It exposes a
        FastAPI `router` that can be mounted into the existing gateway.
        """
        from fastapi import APIRouter, Query, Header, HTTPException
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel, Field
        from typing import Optional, Dict, Any, List
        import os
        import json
        import logging
        from datetime import datetime
        import hashlib

        logger = logging.getLogger(__name__)


        class ExecuteRequest(BaseModel):
            tool_name: str
            arguments: Dict[str, Any] = Field(default_factory=dict)
            dry_run: bool = False
            request_id: Optional[str] = None


        class ExecuteResponse(BaseModel):
            success: bool
            request_id: str
            tool_name: str
            result: Optional[Any] = None
            error: Optional[str] = None
            execution_time_ms: float = 0
            governance_level: Optional[str] = None


        SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
        MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


        def _load_tools_from_main() -> List[Dict[str, Any]]:
            try:
                from main_extended import TOOLS, check_governance
                out = []
                for t in TOOLS:
                    out.append({
                        "name": t.name,
                        "description": getattr(t, "description", ""),
                        "inputSchema": getattr(t, "inputSchema", {}),
                        "governance": check_governance(t.name),
                    })
                return out
            except Exception:
                return []


        def _build_registry() -> Dict[str, Dict[str, Any]]:
            tools = _load_tools_from_main()
            reg: Dict[str, Dict[str, Any]] = {}
            for t in tools:
                name = t.get("name")
                schema = t.get("inputSchema") or {}
                params = []
                for k, v in (schema.get("properties") or {}).items():
                    params.append({
                        "name": k,
                        "type": v.get("type", "string"),
                        "description": v.get("description", ""),
                        "required": k in (schema.get("required") or []),
                    })
                gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
                reg[name] = {
                    "name": name,
                    "description": t.get("description", ""),
                    "parameters": params,
                    "rate_limit_level": gov.get("level", "MEDIUM"),
                    "approval_required": gov.get("level") == "CRITICAL",
                }
            return reg


        REGISTRY = _build_registry()

        router = APIRouter(prefix="/mcp", tags=["mcp"])


        @router.get("/health")
        async def health():
            return {
                "status": "healthy",
                "version": "1.0",
                "protocol_version": "2024-11",
                "mcp_server_available": bool(REGISTRY),
                "firestore_available": False,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }


        """MCP HTTP Adapter — final minimal implementation

        This module provides a compact FastAPI `router` exposing the MCP
        tool execution endpoints and a simple OpenAPI generator for attachment.
        """
        from fastapi import APIRouter, Query, Header, HTTPException
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel, Field
        from typing import Optional, Dict, Any, List
        import os
        import json
        import logging
        from datetime import datetime
        import hashlib

        logger = logging.getLogger(__name__)


        class ExecuteRequest(BaseModel):
            tool_name: str
            arguments: Dict[str, Any] = Field(default_factory=dict)
            dry_run: bool = False
            request_id: Optional[str] = None


        class ExecuteResponse(BaseModel):
            success: bool
            request_id: str
            tool_name: str
            result: Optional[Any] = None
            error: Optional[str] = None
            execution_time_ms: float = 0
            governance_level: Optional[str] = None


        SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
        MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


        def _load_tools_from_main() -> List[Dict[str, Any]]:
            try:
                from main_extended import TOOLS, check_governance
                out = []
                for t in TOOLS:
                    out.append({
                        "name": t.name,
                        "description": getattr(t, "description", ""),
                        "inputSchema": getattr(t, "inputSchema", {}),
                        "governance": check_governance(t.name),
                    })
                return out
            except Exception:
                return []


        def _build_registry() -> Dict[str, Dict[str, Any]]:
            tools = _load_tools_from_main()
            reg: Dict[str, Dict[str, Any]] = {}
            for t in tools:
                name = t.get("name")
                schema = t.get("inputSchema") or {}
                params = []
                for k, v in (schema.get("properties") or {}).items():
                    params.append({
                        "name": k,
                        "type": v.get("type", "string"),
                        "description": v.get("description", ""),
                        "required": k in (schema.get("required") or []),
                    })
                gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
                reg[name] = {
                    "name": name,
                    "description": t.get("description", ""),
                    "parameters": params,
                    "rate_limit_level": gov.get("level", "MEDIUM"),
                    "approval_required": gov.get("level") == "CRITICAL",
                }
            return reg


        REGISTRY = _build_registry()

        router = APIRouter(prefix="/mcp", tags=["mcp"])


        @router.get("/health")
        async def health():
            return {
                "status": "healthy",
                "version": "1.0",
                "protocol_version": "2024-11",
                "mcp_server_available": bool(REGISTRY),
                "firestore_available": False,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }


        @router.get("/tools")
        async def tools():
            return {"count": len(REGISTRY), "tools": list(REGISTRY.values())}


        def _validate_key(x_mcp_key: Optional[str], read_only: bool) -> bool:
            if SAFE_MODE:
                return x_mcp_key == MCP_API_KEY or read_only
            return True


        @router.post("/execute")
        async def execute(req: ExecuteRequest, x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
            start = datetime.utcnow()
            rid = req.request_id or hashlib.sha256(f"{req.tool_name}{start.isoformat()}".encode()).hexdigest()[:16]
            if req.tool_name not in REGISTRY:
                raise HTTPException(status_code=400, detail="Unknown tool")
            tool = REGISTRY[req.tool_name]
            if not _validate_key(x_mcp_key, bool(x_mcp_readonly)):
                raise HTTPException(status_code=401, detail="Unauthorized: X-MCP-KEY invalid or missing")
            if tool.get("approval_required") and not bool(req.arguments.get("_approved", False)):
                try:
                    from memory.helpers import write_local_memory
                    mem = {"type": "tool_request", "tool_name": req.tool_name, "arguments": req.arguments, "requires_approval": True, "approval_status": "pending", "requested_by": x_mcp_key or "anonymous"}
                    mem_id = write_local_memory(mem)
                except Exception:
                    mem_id = None
                return JSONResponse(status_code=200, content={"success": False, "request_id": rid, "tool_name": req.tool_name, "result": {"approval_required": True, "memory_id": mem_id}, "error": "approval_required", "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})
            if req.dry_run:
                return JSONResponse(status_code=200, content={"success": True, "request_id": rid, "tool_name": req.tool_name, "result": {"dry_run": True, "parameters_provided": list(req.arguments.keys())}, "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})
            try:
                from main_extended import server as mcp_server
                if not hasattr(mcp_server, 'call_tool'):
                    raise RuntimeError("MCP server missing call_tool")
                result = await mcp_server.call_tool(req.tool_name, req.arguments)
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                try:
                    if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                        payload = json.loads(result[0].text)
                    else:
                        payload = result
                except Exception:
                    payload = result
                return JSONResponse(status_code=200, content={"success": True, "request_id": rid, "tool_name": req.tool_name, "result": payload, "execution_time_ms": elapsed, "governance_level": tool.get("rate_limit_level")})
            except Exception as e:
                logger.exception("tool execute error")
                return JSONResponse(status_code=500, content={"success": False, "request_id": rid, "tool_name": req.tool_name, "error": str(e), "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})


        @router.post("/execute/{tool_name}")
        async def execute_named(tool_name: str, arguments: Dict[str, Any], dry_run: bool = Query(False), x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
            req = ExecuteRequest(tool_name=tool_name, arguments=arguments, dry_run=dry_run)
            return await execute(req, x_mcp_key=x_mcp_key, x_mcp_readonly=x_mcp_readonly)


        @router.get("/openapi")
        async def openapi(base_url: Optional[str] = Query("http://localhost:8000")):
            paths = {}
            for name, t in REGISTRY.items():
                params = {p['name']: {"type": p.get('type', 'string'), "description": p.get('description', '')} for p in t.get('parameters', [])}
                paths[f"/mcp/execute/{name}"] = {
                    "post": {
                        "summary": f"Execute {name}",
                        "description": t.get('description', ''),
                        "operationId": f"execute_{name}",
                        "requestBody": {"content": {"application/json": {"schema": {"type": "object", "properties": params}}}},
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            spec = {"openapi": "3.0.0", "info": {"title": "Infinity XOS MCP Adapter", "version": "1.0"}, "servers": [{"url": base_url}], "paths": paths}
            spec["x-mcp-attach-ready"] = True
            return JSONResponse(content=spec)
import hashlib

logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    request_id: Optional[str] = None


class ExecuteResponse(BaseModel):
    success: bool
    request_id: str
    tool_name: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    governance_level: Optional[str] = None


SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


class _Bucket:
    def __init__(self, max_tokens: int = 5, refill_seconds: int = 3600):
        from time import time
        self.max_tokens = max_tokens
        self.refill_seconds = refill_seconds
        self.tokens = max_tokens
        self.last = time()

    def can_consume(self, amt: int = 1) -> bool:
        from time import time
        now = time()
        elapsed = now - self.last
        if elapsed > 0:
            rate = self.max_tokens / self.refill_seconds
            self.tokens = min(self.max_tokens, self.tokens + elapsed * rate)
            self.last = now
        if self.tokens >= amt:
            self.tokens -= amt
            return True
        return False


_critical_bucket = _Bucket()


def _load_tools_from_main() -> List[Dict[str, Any]]:
    try:
        from main_extended import TOOLS, check_governance
        out = []
        for t in TOOLS:
            out.append({
                "name": t.name,
                "description": getattr(t, "description", ""),
                "inputSchema": getattr(t, "inputSchema", {}),
                "governance": check_governance(t.name)
            })
        return out
    except Exception:
        return []


def _build_registry() -> Dict[str, Dict[str, Any]]:
    tools = _load_tools_from_main()
    reg: Dict[str, Dict[str, Any]] = {}
    for t in tools:
        name = t.get("name")
        schema = t.get("inputSchema") or {}
        params = []
        for k, v in (schema.get("properties") or {}).items():
            params.append({
                "name": k,
                "type": v.get("type", "string"),
                "description": v.get("description", ""),
                "required": k in (schema.get("required") or [])
            })
        gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
        reg[name] = {
            "name": name,
            "description": t.get("description", ""),
            "parameters": params,
            "rate_limit_level": gov.get("level", "MEDIUM"),
            "approval_required": gov.get("level") == "CRITICAL",
        }
    return reg


REGISTRY = _build_registry()

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0",
        "protocol_version": "2024-11",
        "mcp_server_available": bool(REGISTRY),
        "firestore_available": False,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/tools")
async def tools():
    return {"count": len(REGISTRY), "tools": list(REGISTRY.values())}


def _validate_key(x_mcp_key: Optional[str], read_only: bool) -> bool:
    if SAFE_MODE:
        return x_mcp_key == MCP_API_KEY or read_only
    return True


@router.post("/execute")
async def execute(req: ExecuteRequest, x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    start = datetime.utcnow()
    rid = req.request_id or hashlib.sha256(f"{req.tool_name}{start.isoformat()}".encode()).hexdigest()[:16]
    if req.tool_name not in REGISTRY:
        raise HTTPException(status_code=400, detail="Unknown tool")
    tool = REGISTRY[req.tool_name]
    if not _validate_key(x_mcp_key, bool(x_mcp_readonly)):
        raise HTTPException(status_code=401, detail="Unauthorized: X-MCP-KEY invalid or missing")
    if tool.get("rate_limit_level") == "CRITICAL":
        if not _critical_bucket.can_consume():
            raise HTTPException(status_code=429, detail="Critical operation rate limit exceeded")
    already_approved = bool(req.arguments.get("_approved", False))
    if tool.get("approval_required") and not already_approved:
        try:
            from memory.helpers import write_local_memory
            mem = {"type": "tool_request", "tool_name": req.tool_name, "arguments": req.arguments, "requires_approval": True, "approval_status": "pending", "requested_by": x_mcp_key or "anonymous"}
            mem_id = write_local_memory(mem)
        except Exception:
            mem_id = None
        return JSONResponse(status_code=200, content={"success": False, "request_id": rid, "tool_name": req.tool_name, "result": {"approval_required": True, "memory_id": mem_id}, "error": "approval_required", "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})
    if req.dry_run:
        return JSONResponse(status_code=200, content={"success": True, "request_id": rid, "tool_name": req.tool_name, "result": {"dry_run": True, "parameters_provided": list(req.arguments.keys())}, "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})
    try:
        from main_extended import server as mcp_server
        if not hasattr(mcp_server, 'call_tool'):
            raise RuntimeError("MCP server missing call_tool")
        result = await mcp_server.call_tool(req.tool_name, req.arguments)
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        try:
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                payload = json.loads(result[0].text)
            else:
                payload = result
        except Exception:
            payload = result
        return JSONResponse(status_code=200, content={"success": True, "request_id": rid, "tool_name": req.tool_name, "result": payload, "execution_time_ms": elapsed, "governance_level": tool.get("rate_limit_level")})
    except Exception as e:
        logger.exception("tool execute error")
        return JSONResponse(status_code=500, content={"success": False, "request_id": rid, "tool_name": req.tool_name, "error": str(e), "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})


@router.post("/execute/{tool_name}")
async def execute_named(tool_name: str, arguments: Dict[str, Any], dry_run: bool = Query(False), x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    req = ExecuteRequest(tool_name=tool_name, arguments=arguments, dry_run=dry_run)
    return await execute(req, x_mcp_key=x_mcp_key, x_mcp_readonly=x_mcp_readonly)


@router.get("/openapi")
async def openapi(base_url: Optional[str] = Query("http://localhost:8000")):
    paths = {}
    for name, t in REGISTRY.items():
        params = {p['name']: {"type": p.get('type', 'string'), "description": p.get('description', '')} for p in t.get('parameters', [])}
        paths[f"/mcp/execute/{name}"] = {
            "post": {
                "summary": f"Execute {name}",
                "description": t.get('description', ''),
                "operationId": f"execute_{name}",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object", "properties": params}}}},
                "responses": {"200": {"description": "OK"}}
            }
        }
    spec = {"openapi": "3.0.0", "info": {"title": "Infinity XOS MCP Adapter", "version": "1.0"}, "servers": [{"url": base_url}], "paths": paths}
    spec["x-mcp-attach-ready"] = True
    return JSONResponse(content=spec)
import hashlib

logger = logging.getLogger(__name__)


def _load_tools_from_main() -> List[Dict[str, Any]]:
    try:
        from main_extended import TOOLS, check_governance
        out = []
        for t in TOOLS:
            out.append({
                "name": t.name,
                "description": getattr(t, "description", ""),
                "inputSchema": getattr(t, "inputSchema", {}),
                "governance": check_governance(t.name)
            })
        return out
    except Exception as e:
        logger.debug("main_extended.TOOLS not available: %s", e)
        return []


class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    request_id: Optional[str] = None


class ExecuteResponse(BaseModel):
    success: bool
    request_id: str
    tool_name: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    governance_level: Optional[str] = None


# Config
SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


# Simple in-memory bucket for critical ops
class _Bucket:
    def __init__(self, max_tokens: int, refill_seconds: int):
        from time import time
        self.max_tokens = max_tokens
        self.refill_seconds = refill_seconds
        self.tokens = max_tokens
        self.last = time()

    def can_consume(self, amt: int = 1) -> bool:
        from time import time
        now = time()
        elapsed = now - self.last
        if elapsed > 0:
            rate = self.max_tokens / self.refill_seconds
            self.tokens = min(self.max_tokens, self.tokens + elapsed * rate)
            self.last = now
        if self.tokens >= amt:
            self.tokens -= amt
            return True
        return False


_critical_bucket = _Bucket(5, 3600)


def _build_registry() -> Dict[str, Dict[str, Any]]:
    tools = _load_tools_from_main()
    reg = {}
    for t in tools:
        name = t.get("name")
        schema = t.get("inputSchema") or {}
        params = []
        for k, v in (schema.get("properties") or {}).items():
            params.append({
                "name": k,
                "type": v.get("type", "string"),
                "description": v.get("description", ""),
                "required": k in (schema.get("required") or [])
            })

        gov = t.get("governance") or {"level": "MEDIUM", "allowed": True}
        reg[name] = {
            "name": name,
            "description": t.get("description", ""),
            "parameters": params,
            "rate_limit_level": gov.get("level", "MEDIUM"),
            "approval_required": gov.get("level") == "CRITICAL",
        }
    return reg


REGISTRY = _build_registry()

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0",
        "protocol_version": "2024-11",
        "mcp_server_available": bool(REGISTRY),
        "firestore_available": False,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/tools")
async def tools():
    return {"count": len(REGISTRY), "tools": list(REGISTRY.values())}


def _validate_key(x_mcp_key: Optional[str], read_only: bool) -> bool:
    if SAFE_MODE:
        return x_mcp_key == MCP_API_KEY or read_only
    return True


@router.post("/execute")
async def execute(req: ExecuteRequest, x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    start = datetime.utcnow()
    rid = req.request_id or hashlib.sha256(f"{req.tool_name}{start.isoformat()}".encode()).hexdigest()[:16]

    if req.tool_name not in REGISTRY:
        raise HTTPException(status_code=400, detail="Unknown tool")

    tool = REGISTRY[req.tool_name]

    if not _validate_key(x_mcp_key, bool(x_mcp_readonly)):
        raise HTTPException(status_code=401, detail="Unauthorized: X-MCP-KEY invalid or missing")

    if tool.get("rate_limit_level") == "CRITICAL":
        if not _critical_bucket.can_consume():
            raise HTTPException(status_code=429, detail="Critical operation rate limit exceeded")

    already_approved = bool(req.arguments.get("_approved", False))
    if tool.get("approval_required") and not already_approved:
        try:
            from memory.helpers import write_local_memory
            mem = {"type": "tool_request", "tool_name": req.tool_name, "arguments": req.arguments, "requires_approval": True, "approval_status": "pending", "requested_by": x_mcp_key or "anonymous"}
            mem_id = write_local_memory(mem)
        except Exception as e:
            logger.warning("failed to persist approval request: %s", e)
            mem_id = None

        return JSONResponse(status_code=200, content={"success": False, "request_id": rid, "tool_name": req.tool_name, "result": {"approval_required": True, "memory_id": mem_id}, "error": "approval_required", "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})

    if req.dry_run:
        return JSONResponse(status_code=200, content={"success": True, "request_id": rid, "tool_name": req.tool_name, "result": {"dry_run": True, "parameters_provided": list(req.arguments.keys())}, "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})

    try:
        from main_extended import server as mcp_server
        if not hasattr(mcp_server, 'call_tool'):
            raise RuntimeError("MCP server missing call_tool")

        result = await mcp_server.call_tool(req.tool_name, req.arguments)
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        try:
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                payload = json.loads(result[0].text)
            else:
                payload = result
        except Exception:
            payload = result

        return JSONResponse(status_code=200, content={"success": True, "request_id": rid, "tool_name": req.tool_name, "result": payload, "execution_time_ms": elapsed, "governance_level": tool.get("rate_limit_level")})
    except Exception as e:
        logger.exception("tool execute error")
        return JSONResponse(status_code=500, content={"success": False, "request_id": rid, "tool_name": req.tool_name, "error": str(e), "execution_time_ms": 0, "governance_level": tool.get("rate_limit_level")})


@router.post("/execute/{tool_name}")
async def execute_named(tool_name: str, arguments: Dict[str, Any], dry_run: bool = Query(False), x_mcp_key: Optional[str] = Header(None), x_mcp_readonly: Optional[bool] = Header(False)):
    req = ExecuteRequest(tool_name=tool_name, arguments=arguments, dry_run=dry_run)
    return await execute(req, x_mcp_key=x_mcp_key, x_mcp_readonly=x_mcp_readonly)


@router.get("/openapi")
async def openapi(base_url: Optional[str] = Query("http://localhost:8000")):
    paths = {}
    for name, t in REGISTRY.items():
        params = {p['name']: {"type": p.get('type', 'string'), "description": p.get('description', '')} for p in t.get('parameters', [])}
        paths[f"/mcp/execute/{name}"] = {
            "post": {
                "summary": f"Execute {name}",
                "description": t.get('description', ''),
                "operationId": f"execute_{name}",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object", "properties": params}}}},
                "responses": {"200": {"description": "OK"}}
            }
        }

    spec = {"openapi": "3.0.0", "info": {"title": "Infinity XOS MCP Adapter", "version": "1.0"}, "servers": [{"url": base_url}], "paths": paths}
    spec["x-mcp-attach-ready"] = True
    return JSONResponse(content=spec)
            logger.error(f"Tool execution failed: {request.tool_name} - {str(e)}")

            return ExecuteResponse(
                success=False,
                request_id=request_id,
                tool_name=request.tool_name,
                error=str(e),
                execution_time_ms=execution_time,
                governance_level="MEDIUM"
            )

    async def _invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke tool via MCP server"""
        try:
            # Call tool via MCP server's call_tool method
            result = await self.mcp_server.call_tool(tool_name, arguments)

            # Extract text content from TextContent objects
            if isinstance(result, list) and len(result) > 0:
                content = result[0]
                if hasattr(content, 'text'):
                    try:
                        return json.loads(content.text)
                    except:
                        return {"output": content.text}

            return result
        except Exception as e:
            logger.error(f"MCP invocation error: {str(e)}")
            raise RuntimeError(f"Tool execution failed: {str(e)}")

    def generate_openapi_spec(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Generate OpenAPI 3.0 schema from tool registry"""

        # Group tools by category
        tools_by_category = {}
        for tool in self.tools_registry.values():
            if tool.category not in tools_by_category:
                tools_by_category[tool.category] = []
            tools_by_category[tool.category].append(tool)

        # Build paths
        paths = {}

        # POST /mcp/execute/{tool_name}
        for tool_name, tool_def in self.tools_registry.items():
            path = f"/mcp/execute/{tool_name}"

            # Build parameter schema
            properties = {}
            required_params = []

            for param in tool_def.parameters:
                schema = {
                    "type": param.type,
                    "description": param.description
                }
                if param.enum:
                    schema["enum"] = param.enum
                if param.default is not None:
                    schema["default"] = param.default

                properties[param.name] = schema

                if param.required:
                    required_params.append(param.name)

            paths[path] = {
                "post": {
                    "summary": f"Execute {tool_name}",
                    "description": tool_def.description,
                    "tags": [tool_def.category],
                    "operationId": f"execute_{tool_name}",
                    "parameters": [
                        {
                            "name": "dry_run",
                            "in": "query",
                            "description": "Dry-run mode (no execution)",
                            "schema": {"type": "boolean", "default": False}
                        },
                        {
                            "name": "X-MCP-KEY",
                            "in": "header",
                            "description": "MCP API key",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "X-MCP-ReadOnly",
                            "in": "header",
                            "description": "Read-only mode (blocks write operations)",
                            "schema": {"type": "boolean"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": properties,
                                    "required": required_params
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Tool execution result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "request_id": {"type": "string"},
                                            "tool_name": {"type": "string"},
                                            "result": {"type": "object"},
                                            "error": {"type": "string"},
                                            "execution_time_ms": {"type": "number"},
                                            "governance_level": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Invalid request"},
                        "401": {"description": "Unauthorized"},
                        "429": {"description": "Rate limited"}
                    }
                }
            }

        # Add discovery endpoints
        paths["/mcp/health"] = {
            "get": {
                "summary": "MCP Adapter Health",
                "tags": ["System"],
                "operationId": "get_health",
                "responses": {
                    "200": {
                        "description": "Health status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "version": {"type": "string"},
                                        "protocol_version": {"type": "string"},
                                        "mcp_server_available": {"type": "boolean"},
                                        "firestore_available": {"type": "boolean"},
                                        "timestamp": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        paths["/mcp/tools"] = {
            "get": {
                "summary": "List All Tools",
                "tags": ["System"],
                "operationId": "list_tools",
                "responses": {
                    "200": {
                        "description": "List of available tools",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "description": {"type": "string"},
                                            "category": {"type": "string"},
                                            "parameters": {"type": "array"},
                                            "rate_limit_level": {"type": "string"},
                                            "requires_auth": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        paths["/mcp/schema"] = {
            "get": {
                "summary": "Get OpenAPI Schema",
                "tags": ["System"],
                "operationId": "get_schema",
                "responses": {
                    "200": {
                        "description": "OpenAPI 3.0 schema",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        }

        # Build OpenAPI spec
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Infinity XOS MCP HTTP Adapter",
                "description": "HTTP/OpenAPI interface for Infinity XOS MCP tools (58+)",
                "version": MCP_API_VERSION,
                "x-mcp-protocol": MCP_PROTOCOL_VERSION,
                "contact": {
                    "name": "Infinity XOne Systems",
                    "url": "https://infinityxonesystems.com"
                }
            },
            "servers": [
                {
                    "url": base_url,
                    "description": "MCP Adapter Server"
                }
            ],
            "paths": paths,
            "tags": (
                [{"name": "System", "description": "System and discovery endpoints"}]
                + [{"name": cat, "description": f"{cat} tools"} for cat in sorted(tools_by_category.keys())]
            ),
            "components": {
                "securitySchemes": {
                    "MCP-API-Key": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-MCP-KEY",
                        "description": "MCP API key for authentication"
                    }
                },
                "schemas": {
                    "ExecuteRequest": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "arguments": {"type": "object"},
                            "dry_run": {"type": "boolean"},
                            "request_id": {"type": "string"}
                        },
                        "required": ["tool_name"]
                    },
                    "ExecuteResponse": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "request_id": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "result": {"type": "object"},
                            "error": {"type": "string"},
                            "execution_time_ms": {"type": "number"},
                            "governance_level": {"type": "string"}
                        }
                    }
                }
            },
            "x-stats": {
                "total_tools": len(self.tools_registry),
                "tools_by_category": {
                    cat: len(tools)
                    for cat, tools in tools_by_category.items()
                }
            }
        }

        return spec
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ExecuteResponse(
                success=True,
                request_id=request_id,
                tool_name=request.tool_name,
                result=result,
                execution_time_ms=execution_time,
                governance_level=gov_check.get("level")
            )
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Tool execution failed: {request.tool_name} - {str(e)}")
            
            return ExecuteResponse(
                success=False,
                request_id=request_id,
                tool_name=request.tool_name,
                error=str(e),
                execution_time_ms=execution_time,
                governance_level="MEDIUM"
            )
    
    async def _invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke tool via MCP server"""
        try:
            # Call tool via MCP server's call_tool method
            result = await self.mcp_server.call_tool(tool_name, arguments)
            
            # Extract text content from TextContent objects
            if isinstance(result, list) and len(result) > 0:
                content = result[0]
                if hasattr(content, 'text'):
                    try:
                        return json.loads(content.text)
                    except:
                        return {"output": content.text}
            
            return result
        except Exception as e:
            logger.error(f"MCP invocation error: {str(e)}")
            raise RuntimeError(f"Tool execution failed: {str(e)}")
    
    def generate_openapi_spec(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Generate OpenAPI 3.0 schema from tool registry"""
        
        # Group tools by category
        tools_by_category = {}
        for tool in self.tools_registry.values():
            if tool.category not in tools_by_category:
                tools_by_category[tool.category] = []
            tools_by_category[tool.category].append(tool)
        
        # Build paths
        paths = {}
        
        # POST /mcp/execute/{tool_name}
        for tool_name, tool_def in self.tools_registry.items():
            path = f"/mcp/execute/{tool_name}"
            
            # Build parameter schema
            properties = {}
            required_params = []
            
            for param in tool_def.parameters:
                schema = {
                    "type": param.type,
                    "description": param.description
                }
                if param.enum:
                    schema["enum"] = param.enum
                if param.default is not None:
                    schema["default"] = param.default
                
                properties[param.name] = schema
                
                if param.required:
                    required_params.append(param.name)
            
            paths[path] = {
                "post": {
                    "summary": f"Execute {tool_name}",
                    "description": tool_def.description,
                    "tags": [tool_def.category],
                    "operationId": f"execute_{tool_name}",
                    "parameters": [
                        {
                            "name": "dry_run",
                            "in": "query",
                            "description": "Dry-run mode (no execution)",
                            "schema": {"type": "boolean", "default": False}
                        },
                        {
                            "name": "X-MCP-KEY",
                            "in": "header",
                            "description": "MCP API key",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "X-MCP-ReadOnly",
                            "in": "header",
                            "description": "Read-only mode (blocks write operations)",
                            "schema": {"type": "boolean"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": properties,
                                    "required": required_params
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Tool execution result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "request_id": {"type": "string"},
                                            "tool_name": {"type": "string"},
                                            "result": {"type": "object"},
                                            "error": {"type": "string"},
                                            "execution_time_ms": {"type": "number"},
                                            "governance_level": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Invalid request"},
                        "401": {"description": "Unauthorized"},
                        "429": {"description": "Rate limited"}
                    }
                }
            }
        
        # Add discovery endpoints
        paths["/mcp/health"] = {
            "get": {
                "summary": "MCP Adapter Health",
                "tags": ["System"],
                "operationId": "get_health",
                "responses": {
                    "200": {
                        "description": "Health status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "version": {"type": "string"},
                                        "protocol_version": {"type": "string"},
                                        "mcp_server_available": {"type": "boolean"},
                                        "firestore_available": {"type": "boolean"},
                                        "timestamp": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        paths["/mcp/tools"] = {
            "get": {
                "summary": "List All Tools",
                "tags": ["System"],
                "operationId": "list_tools",
                "responses": {
                    "200": {
                        "description": "List of available tools",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "description": {"type": "string"},
                                            "category": {"type": "string"},
                                            "parameters": {"type": "array"},
                                            "rate_limit_level": {"type": "string"},
                                            "requires_auth": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        paths["/mcp/schema"] = {
            "get": {
                "summary": "Get OpenAPI Schema",
                "tags": ["System"],
                "operationId": "get_schema",
                "responses": {
                    "200": {
                        "description": "OpenAPI 3.0 schema",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        }
        
        # Build OpenAPI spec
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Infinity XOS MCP HTTP Adapter",
                "description": "HTTP/OpenAPI interface for Infinity XOS MCP tools (58+)",
                "version": MCP_API_VERSION,
                "x-mcp-protocol": MCP_PROTOCOL_VERSION,
                "contact": {
                    "name": "Infinity XOne Systems",
                    "url": "https://infinityxonesystems.com"
                }
            },
            "servers": [
                {
                    "url": base_url,
                    "description": "MCP Adapter Server"
                }
            ],
            "paths": paths,
            "tags": (
                [{"name": "System", "description": "System and discovery endpoints"}]
                + [{"name": cat, "description": f"{cat} tools"} for cat in sorted(tools_by_category.keys())]
            ),
            "components": {
                "securitySchemes": {
                    "MCP-API-Key": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-MCP-KEY",
                        "description": "MCP API key for authentication"
                    }
                },
                "schemas": {
                    "ExecuteRequest": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "arguments": {"type": "object"},
                            "dry_run": {"type": "boolean"},
                            "request_id": {"type": "string"}
                        },
                        "required": ["tool_name"]
                    },
                    "ExecuteResponse": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "request_id": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "result": {"type": "object"},
                            "error": {"type": "string"},
                            "execution_time_ms": {"type": "number"},
                            "governance_level": {"type": "string"}
                        }
                    }
                }
            },
            "x-stats": {
                "total_tools": len(self.tools_registry),
                "tools_by_category": {
                    cat: len(tools)
                    for cat, tools in tools_by_category.items()
                }
            }
        }
        
        return spec


# ===== GLOBAL ADAPTER INSTANCE =====
mcp_adapter = MCPHTTPAdapter()


# ===== FASTAPI ROUTER =====
router = APIRouter(prefix="/mcp", tags=["MCP Adapter"])


@router.get("/health")
async def health_check():
    """MCP Adapter health status"""
    health = mcp_adapter.health()
    return health.model_dump()


@router.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    tools = mcp_adapter.list_tools()
    return {
        "count": len(tools),
        "tools": [tool.model_dump() for tool in tools]
    }


@router.post("/execute")
async def execute_tool(
    request: ExecuteRequest,
    x_mcp_key: Optional[str] = Header(None),
    x_mcp_readonly: Optional[bool] = Header(False)
):
    """Execute an MCP tool"""
    result = await mcp_adapter.execute_tool(
        request,
        mcp_key=x_mcp_key,
        read_only=x_mcp_readonly or False
    )
    
    status_code = 200 if result.success else 400
    return JSONResponse(
        content=result.model_dump(exclude_none=True),
        status_code=status_code
    )


@router.get("/schema")
async def get_schema(base_url: Optional[str] = Query("http://localhost:8000")):
    """Get OpenAPI 3.0 schema for all tools"""
    spec = mcp_adapter.generate_openapi_spec(base_url=base_url)
    return spec


@router.get("/schema.json")
async def get_schema_json():
    """Get OpenAPI schema as downloadable JSON"""
    spec = mcp_adapter.generate_openapi_spec()
    return JSONResponse(
        content=spec,
        headers={
            "Content-Disposition": "attachment; filename=mcp-openapi.json"
        }
    )


@router.get("/openapi")
async def get_openapi(base_url: Optional[str] = Query("http://localhost:8000")):
    """Compatibility endpoint for Custom GPT attachment: returns OpenAPI 3.x spec"""
    spec = mcp_adapter.generate_openapi_spec(base_url=base_url)
    # Attach metadata required by Custom GPT builders
    spec["x-mcp-attach-ready"] = True
    spec["servers"] = [{"url": base_url}]
    return JSONResponse(content=spec)


@router.get("/schema.yaml")
async def get_schema_yaml():
    """Get OpenAPI schema as downloadable YAML"""
    try:
        import yaml
        spec = mcp_adapter.generate_openapi_spec()
        yaml_content = yaml.dump(spec, default_flow_style=False)
        return {
            "content": yaml_content,
            "format": "yaml"
        }
    except ImportError:
        return {
            "error": "PyYAML not installed",
            "format": "json",
            "content": mcp_adapter.generate_openapi_spec()
        }


# ===== TOOL-SPECIFIC EXECUTION ENDPOINTS =====
# Dynamically create execution endpoints for each tool

@router.post("/execute/{tool_name}")
async def execute_named_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    dry_run: bool = Query(False),
    x_mcp_key: Optional[str] = Header(None),
    x_mcp_readonly: Optional[bool] = Header(False)
):
    """Execute a specific named tool"""
    request = ExecuteRequest(
        tool_name=tool_name,
        arguments=arguments,
        dry_run=dry_run
    )
    
    result = await mcp_adapter.execute_tool(
        request,
        mcp_key=x_mcp_key,
        read_only=x_mcp_readonly or False
    )
    
    status_code = 200 if result.success else 400
    return JSONResponse(
        content=result.model_dump(exclude_none=True),
        status_code=status_code
    )


@router.get("/stats")
async def get_stats():
    """Get MCP adapter statistics"""
    return {
        "adapter_version": MCP_API_VERSION,
        "protocol_version": MCP_PROTOCOL_VERSION,
        "total_tools": len(mcp_adapter.tools_registry),
        "mcp_server_available": mcp_adapter.mcp_server_available,
        "tools_by_category": {
            cat: len([t for t in mcp_adapter.tools_registry.values() 
                     if t.category == cat])
            for cat in set(t.category for t in mcp_adapter.tools_registry.values())
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/categories")
async def get_categories():
    """Get tool categories"""
    categories = {}
    for tool in mcp_adapter.tools_registry.values():
        if tool.category not in categories:
            categories[tool.category] = []
        categories[tool.category].append({
            "name": tool.name,
            "description": tool.description,
            "governance_level": tool.rate_limit_level
        })
    
    return {
        "total_categories": len(categories),
        "categories": categories
    }
