#!/usr/bin/env python3
"""Orchestrator service exposing GPT-controllable endpoints.

Endpoints: /health, /read, /write, /analyze, /simulate, /predict, /crawl
"""
import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

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


class ExecuteRequest(BaseModel):
    command: str
    payload: dict | None = None
    provider: str | None = None
    action: str | None = None


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
        "analysis": req.payload,
    }


@app.post("/simulate")
def simulate(req: AnalyzeRequest):
    return {
        "status": "ok",
        "provider": req.provider or "generic",
        "action": req.action or "simulate",
        "simulation": req.payload,
    }


@app.post("/predict")
def predict(req: PredictRequest):
    r = requests.post(
        f"{GATEWAY}/predict", json={"model": req.model, "input": req.input}, timeout=15
    )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.post("/crawl")
def crawl(req: CrawlRequest):
    r = requests.post(
        f"{GATEWAY}/crawl", json={"url": req.url, "depth": req.depth}, timeout=30
    )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return (
        r.json()
        if r.headers.get("content-type", "").startswith("application/json")
        else {"status": r.status_code, "body": r.text[:200]}
    )


@app.post("/execute")
def execute(req: ExecuteRequest):
    cmd = req.command.lower()
    payload = req.payload or {}

    # Provider-aware routing
    if req.provider:
        provider = req.provider.lower()
        action = (req.action or cmd).lower()

        if provider == "github":
            return handle_github(action, payload)

        if provider == "workspace":
            # Workspace routes through gateway sheets/calendar endpoints
            if action in {
                "sheets_append",
                "sheets_read",
                "sheets_update",
                "sheets_clear",
            }:
                return proxy_gateway_sheets(action, payload)
            if action in {
                "calendar_list",
                "calendar_create",
                "calendar_update",
                "calendar_delete",
                "calendar_from_prediction",
            }:
                return proxy_gateway_calendar(action, payload)
            raise HTTPException(
                status_code=400, detail=f"Unsupported workspace action: {action}"
            )

        if provider == "gateway":
            return proxy_gateway(cmd, payload)

        # Unsupported providers return explicit 400
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    if cmd == "read":
        return read(ReadRequest(**payload))
    if cmd == "write":
        return write(WriteRequest(**payload))
    if cmd == "analyze":
        return analyze(AnalyzeRequest(**payload))
    if cmd == "simulate":
        return simulate(AnalyzeRequest(**payload))
    if cmd == "predict":
        return predict(PredictRequest(**payload))
    if cmd == "crawl":
        return crawl(CrawlRequest(**payload))

    raise HTTPException(status_code=400, detail=f"Unknown command: {cmd}")


# ---------- Provider helpers ----------


def gh_request(
    method: str, path: str, *, json_body: dict | None = None, params: dict | None = None
):
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=401, detail="GITHUB_TOKEN not configured")
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.request(
        method, url, headers=headers, json=json_body, params=params, timeout=20
    )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    if r.headers.get("content-type", "").startswith("application/json"):
        return r.json()
    return {"status": r.status_code, "body": r.text[:500]}


def handle_github(action: str, payload: dict):
    repo = payload.get("repo")
    if not repo:
        raise HTTPException(
            status_code=400, detail="repo is required for GitHub actions"
        )

    if action == "create_issue":
        title = payload.get("title")
        body = payload.get("body", "")
        if not title:
            raise HTTPException(status_code=400, detail="title is required")
        return gh_request(
            "POST", f"/repos/{repo}/issues", json_body={"title": title, "body": body}
        )

    if action == "comment_issue":
        issue = payload.get("issue_number")
        comment = payload.get("comment")
        if not issue or not comment:
            raise HTTPException(
                status_code=400, detail="issue_number and comment are required"
            )
        return gh_request(
            "POST",
            f"/repos/{repo}/issues/{issue}/comments",
            json_body={"body": comment},
        )

    if action == "list_issues":
        state = payload.get("state", "open")
        return gh_request("GET", f"/repos/{repo}/issues", params={"state": state})

    if action == "get_repo":
        return gh_request("GET", f"/repos/{repo}")

    if action == "dispatch_workflow":
        workflow = payload.get("workflow")
        ref = payload.get("ref", "main")
        inputs = payload.get("inputs", {})
        if not workflow:
            raise HTTPException(status_code=400, detail="workflow is required")
        return gh_request(
            "POST",
            f"/repos/{repo}/actions/workflows/{workflow}/dispatches",
            json_body={"ref": ref, "inputs": inputs},
        )

    raise HTTPException(status_code=400, detail=f"Unsupported GitHub action: {action}")


def proxy_gateway_sheets(action: str, payload: dict):
    sheet_id = payload.get("sheet_id")
    range_name = payload.get("range_name")
    if not sheet_id or not range_name:
        raise HTTPException(
            status_code=400, detail="sheet_id and range_name are required"
        )

    endpoint_map = {
        "sheets_append": "/sheets/append",
        "sheets_read": "/sheets/read",
        "sheets_update": "/sheets/update",
        "sheets_clear": "/sheets/clear",
    }
    url = f"{GATEWAY}{endpoint_map[action]}"
    method = "post" if action != "sheets_read" else "get"
    payload_map = {
        "sheet_id": sheet_id,
        "range_name": range_name,
    }
    if action in {"sheets_append", "sheets_update"}:
        values = payload.get("values")
        if not values:
            raise HTTPException(
                status_code=400, detail="values required for append/update"
            )
        payload_map["values"] = values
    return call_gateway(method, url, payload_map)


def proxy_gateway_calendar(action: str, payload: dict):
    calendar_id = payload.get("calendar_id", "primary")
    endpoint_map = {
        "calendar_list": "/calendar/events",
        "calendar_create": "/calendar/create",
        "calendar_update": "/calendar/update",
        "calendar_delete": "/calendar/delete",
        "calendar_from_prediction": "/calendar/from_prediction",
    }
    url = f"{GATEWAY}{endpoint_map[action]}"
    method = "get" if action == "calendar_list" else "post"
    payload_map = {k: v for k, v in payload.items() if v is not None}
    if action == "calendar_list":
        payload_map.setdefault("calendar_id", calendar_id)
    else:
        payload_map["calendar_id"] = calendar_id
    return call_gateway(method, url, payload_map)


def proxy_gateway(cmd: str, payload: dict):
    cmd = cmd.lower()
    if cmd == "predict":
        return call_gateway("post", f"{GATEWAY}/predict", payload)
    if cmd == "crawl":
        return call_gateway("post", f"{GATEWAY}/crawl", payload)
    if cmd == "simulate":
        return call_gateway("post", f"{GATEWAY}/simulate", payload)
    if cmd == "read":
        resource = payload.get("resource") or payload.get("target")
        if not resource:
            raise HTTPException(status_code=400, detail="resource is required")
        return call_gateway("post", f"{GATEWAY}/read/{resource}", payload)
    if cmd == "write":
        resource = payload.get("resource") or payload.get("target")
        if not resource:
            raise HTTPException(status_code=400, detail="resource is required")
        return call_gateway("post", f"{GATEWAY}/write/{resource}", payload)
    if cmd == "analyze":
        resource = payload.get("resource") or payload.get("target")
        if not resource:
            raise HTTPException(status_code=400, detail="resource is required")
        return call_gateway("post", f"{GATEWAY}/analyze/{resource}", payload)
    raise HTTPException(status_code=400, detail=f"Unsupported gateway command: {cmd}")


def call_gateway(method: str, url: str, payload: dict):
    method = method.lower()
    try:
        if method == "get":
            r = requests.get(url, params=payload, timeout=30)
        else:
            r = requests.post(url, json=payload, timeout=30)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return (
            r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else {"status": r.status_code, "body": r.text[:500]}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gateway call failed: {e}")


def serve():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))


if __name__ == "__main__":
    serve()
