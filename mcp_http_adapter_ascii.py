"""MCP HTTP Adapter (ASCII-only, clean)

Exposes FastAPI APIRouter under /mcp with:
- GET /mcp/health
- GET /mcp/tools
- POST /mcp/execute
- POST /mcp/execute/{tool_name}
- GET /mcp/openapi

SAFE_MODE via X-MCP-KEY, dry-run support, CRITICAL approval persistence
via memory.helpers.write_local_memory, and minimal OpenAPI with x-mcp-attach-ready.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
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


SAFE_MODE = os.environ.get("SAFE_MODE", "true").lower() in ("1", "true", "yes")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "default-key-change-me")


def _load_tools_from_main() -> List[Dict[str, Any]]:
    try:
        from main_extended import TOOLS, check_governance

        out = []
        for t in TOOLS:
            out.append(
                {
                    "name": getattr(t, "name", None),
                    "description": getattr(t, "description", ""),
                    "inputSchema": getattr(t, "inputSchema", {}),
                    "governance": check_governance(getattr(t, "name", "")),
                }
            )
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
            params.append(
                {
                    "name": k,
                    "type": v.get("type", "string"),
                    "description": v.get("description", ""),
                    "required": k in (schema.get("required") or []),
                }
            )
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
            return False
        raise HTTPException(
            status_code=401, detail="Missing or invalid X-MCP-KEY header"
        )
    return True


async def _invoke_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    try:
        from main_extended import server

        fn = getattr(server, "call_tool", None)
        if fn is None:
            raise RuntimeError("server.call_tool is not available")
        if asyncio.iscoroutinefunction(fn):
            return await fn(tool_name, arguments)
        return await asyncio.to_thread(fn, tool_name, arguments)
    except Exception:
        logger.exception("error invoking tool %s", tool_name)
        raise


def _persist_approval_request(
    tool_name: str, arguments: Dict[str, Any], metadata: Dict[str, Any]
):
    try:
        from memory import helpers as mem_helpers

        doc = {
            "session_hash": hashlib.sha256(
                f"{tool_name}{json.dumps(arguments, sort_keys=True)}".encode()
            ).hexdigest(),
            "type": "approval_request",
            "content": {
                "tool_name": tool_name,
                "arguments": arguments,
                "metadata": metadata,
            },
            "confidence": 1.0,
            "sources": [],
            "prompt_hash": None,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        if hasattr(mem_helpers, "write_local_memory"):
            try:
                mem_helpers.write_local_memory(doc)
            except TypeError:
                mem_helpers.write_local_memory(doc.get("session_hash"), doc)
    except Exception:
        logger.exception("failed to persist approval request for %s", tool_name)


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "mcp_server_available": bool(REGISTRY),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/tools")
async def list_tools():
    return JSONResponse(content={"tools": list(REGISTRY.values())})


@router.post("/execute")
async def execute(
    req: ExecuteRequest,
    x_mcp_key: Optional[str] = Header(None),
    x_mcp_readonly: Optional[bool] = Header(False),
):
    tool = REGISTRY.get(req.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"tool not found: {req.tool_name}")

    gov_level = tool.get("rate_limit_level")
    approval_required = tool.get("approval_required", False)

    # Allow dry-run without authentication to inspect parameters safely
    if req.dry_run:
        return JSONResponse(
            content={
                "success": True,
                "request_id": req.request_id or "dryrun",
                "tool_name": req.tool_name,
                "result": {
                    "parameters": tool.get("parameters", []),
                    "governance_level": gov_level,
                    "approval_required": approval_required,
                },
            }
        )

    # Enforce SAFE_MODE for actual execution
    try:
        _validate_key(x_mcp_key, read_only=bool(x_mcp_readonly))
    except HTTPException:
        if not x_mcp_readonly:
            raise

    if approval_required and not getattr(req, "_approved", False):
        _persist_approval_request(
            req.tool_name, req.arguments, {"governance_level": gov_level}
        )
        return JSONResponse(
            status_code=202,
            content={
                "success": False,
                "request_id": req.request_id or "approval_required",
                "tool_name": req.tool_name,
                "error": "approval_required",
                "governance_level": gov_level,
            },
        )

    if req.background:

        async def _bg():
            try:
                await _invoke_tool(req.tool_name, req.arguments)
            except Exception:
                logger.exception("background execution failed for %s", req.tool_name)

        asyncio.create_task(_bg())
        return JSONResponse(
            status_code=202,
            content={
                "success": True,
                "request_id": req.request_id or "background",
                "tool_name": req.tool_name,
            },
        )

    start = datetime.utcnow()
    try:
        result = await _invoke_tool(req.tool_name, req.arguments)
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000.0
        return JSONResponse(
            content={
                "success": True,
                "request_id": req.request_id or "ok",
                "tool_name": req.tool_name,
                "result": result,
                "execution_time_ms": elapsed,
                "governance_level": gov_level,
            }
        )
    except Exception as e:
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000.0
        logger.exception("tool execute error")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "request_id": req.request_id or "error",
                "tool_name": req.tool_name,
                "error": str(e),
                "execution_time_ms": elapsed,
                "governance_level": gov_level,
            },
        )


@router.post("/execute/{tool_name}")
async def execute_named(
    tool_name: str,
    arguments: Dict[str, Any],
    dry_run: bool = Query(False),
    x_mcp_key: Optional[str] = Header(None),
    x_mcp_readonly: Optional[bool] = Header(False),
):
    req = ExecuteRequest(tool_name=tool_name, arguments=arguments, dry_run=dry_run)
    return await execute(req, x_mcp_key=x_mcp_key, x_mcp_readonly=x_mcp_readonly)


@router.get("/openapi")
async def openapi(base_url: Optional[str] = Query("http://localhost:8000")):
    paths = {}
    for name, t in REGISTRY.items():
        params = {
            p["name"]: {
                "type": p.get("type", "string"),
                "description": p.get("description", ""),
            }
            for p in t.get("parameters", [])
        }
        paths[f"/mcp/execute/{name}"] = {
            "post": {
                "summary": f"Execute {name}",
                "description": t.get("description", ""),
                "operationId": f"execute_{name}",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": params}
                        }
                    }
                },
                "responses": {"200": {"description": "OK"}},
            }
        }
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Infinity XOS MCP Adapter", "version": "1.0"},
        "servers": [{"url": base_url}],
        "paths": paths,
    }
    spec["x-mcp-attach-ready"] = True
    return JSONResponse(content=spec)
