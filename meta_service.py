from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import databases
import sqlalchemy
import json
import threading
import pyttsx3
import base64
import google.auth
from google.cloud import texttospeech
from google.cloud import secretmanager
import tempfile
import pathlib
from urllib.parse import urlparse

from crawler import crawl
from safety import (
    SCRAPER_USER_AGENT,
    RateLimiter,
    filter_allowed_domains,
    robots_can_fetch_httpx,
    validate_url,
)
from scraper import scrape

app = FastAPI(title="Infinity XOS Meta Service")
API_KEY = os.environ.get("MCP_API_KEY")
rate_limiter = RateLimiter()
ALLOWED_HTTP_METHODS = {"GET", "POST", "HEAD"}

def check_auth(request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.split(" ", 1)[1]
    if API_KEY and token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")


async def validate_outbound_url(url: str) -> str:
    try:
        host = validate_url(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    allowed = await robots_can_fetch_httpx(url, user_agent=SCRAPER_USER_AGENT)
    if not allowed:
        raise HTTPException(status_code=403, detail="Blocked by robots.txt")
    await rate_limiter.wait(host)
    return host


def sanitize_headers(headers: dict) -> dict:
    cleaned = {k: v for k, v in headers.items() if k.lower() not in {"host", "authorization", "user-agent"}}
    cleaned["User-Agent"] = SCRAPER_USER_AGENT
    return cleaned

DB_PATH = os.environ.get("MCP_MEMORY_DB", "sqlite:///./mcp_memory.db")
database = databases.Database(DB_PATH)
metadata = sqlalchemy.MetaData()

memory_table = sqlalchemy.Table(
    "memory",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("namespace", sqlalchemy.String, index=True),
    sqlalchemy.Column("key", sqlalchemy.String, index=True),
    sqlalchemy.Column("value", sqlalchemy.Text),
)

# Jobs table for workers
job_table = sqlalchemy.Table(
    "jobs",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("type", sqlalchemy.String, index=True),
    sqlalchemy.Column("action", sqlalchemy.String),
    sqlalchemy.Column("payload", sqlalchemy.Text),
    sqlalchemy.Column("status", sqlalchemy.String, default="pending", index=True),
    sqlalchemy.Column("result", sqlalchemy.Text, nullable=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now()),
)


engine = sqlalchemy.create_engine(DB_PATH.replace("sqlite:///", "sqlite:///"), connect_args={"check_same_thread": False})
metadata.create_all(engine)

@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/memory/set")
async def memory_set(request: Request):
    check_auth(request)
    body = await request.json()
    ns = body.get("namespace", "default")
    key = body.get("key")
    value = body.get("value")
    if not key:
        raise HTTPException(status_code=400, detail="Missing 'key' in body")
    query = memory_table.insert().values(namespace=ns, key=key, value=json.dumps(value))
    record_id = await database.execute(query)
    return JSONResponse({"id": record_id, "namespace": ns, "key": key})


@app.get("/memory/get")
async def memory_get(request: Request, key: str, namespace: str = "default"):
    check_auth(request)
    query = memory_table.select().where(memory_table.c.key == key).where(memory_table.c.namespace == namespace)
    row = await database.fetch_one(query)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse({"id": row["id"], "namespace": row["namespace"], "key": row["key"], "value": json.loads(row["value"])})


@app.post("/memory/list")
async def memory_list(request: Request):
    check_auth(request)
    body = await request.json()
    namespace = body.get("namespace", "default")
    q = memory_table.select().where(memory_table.c.namespace == namespace)
    rows = await database.fetch_all(q)
    return JSONResponse([{"id": r["id"], "key": r["key"], "value": json.loads(r["value"])} for r in rows])


@app.post("/omni")
async def omni_gateway(request: Request):
    """Smart routing: if request contains 'memory' action route to memory, otherwise proxy to meta endpoints."""
    check_auth(request)
    body = await request.json()
    action = body.get("action")
    if not action:
        raise HTTPException(status_code=400, detail="Missing 'action' in body")
    # Simple routing rules
    if action.startswith("memory."):
        # map memory.get/memory.set/memory.list
        act = action.split(".", 1)[1]
        if act == "get":
            key = body.get("key")
            namespace = body.get("namespace", "default")
            # Call internal endpoint
            url = f"http://127.0.0.1:8000/memory/get?key={key}&namespace={namespace}"
            async with httpx.AsyncClient() as client:
                r = await client.get(url, headers={"authorization": request.headers.get("authorization")})
                return JSONResponse(r.json(), status_code=r.status_code)
        elif act == "set":
            async with httpx.AsyncClient() as client:
                r = await client.post("http://127.0.0.1:8000/memory/set", json={"namespace": body.get("namespace","default"), "key": body.get("key"), "value": body.get("value")}, headers={"authorization": request.headers.get("authorization")})
                return JSONResponse(r.json(), status_code=r.status_code)
        elif act == "list":
            async with httpx.AsyncClient() as client:
                r = await client.post("http://127.0.0.1:8000/memory/list", json={"namespace": body.get("namespace","default")}, headers={"authorization": request.headers.get("authorization")})
                return JSONResponse(r.json(), status_code=r.status_code)
        else:
            raise HTTPException(status_code=400, detail="Unknown memory action")
    else:
        # fallback: proxy to meta endpoints (meta prefix mapping)
        target = body.get("target")
        if not target:
            raise HTTPException(status_code=400, detail="Missing 'target' for non-memory actions")
        async with httpx.AsyncClient() as client:
            method = body.get("method","POST")
            r = await client.request(method, target, json=body.get("payload", {}), headers={"authorization": request.headers.get("authorization")})
            return JSONResponse({"status_code": r.status_code, "body": r.json() if r.headers.get("content-type","" ).startswith("application/json") else r.text}, status_code=r.status_code)



def _speak_sync(text: str):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


@app.post("/voice/speak")
async def voice_speak(request: Request):
    """Speak text using local TTS (pyttsx3). Runs speak in a thread to avoid blocking."""
    check_auth(request)
    body = await request.json()
    text = body.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' in body")
    # Run in background thread
    t = threading.Thread(target=_speak_sync, args=(text,), daemon=True)
    t.start()
    return JSONResponse({"status": "queued", "text_length": len(text)})



@app.post("/voice/sol")
async def voice_sol(request: Request):
    """Synthesize speech using Google Cloud Text-to-Speech and return base64-encoded audio.
    Uses GOOGLE_APPLICATION_CREDENTIALS env var or default ADC. Returns audioContent as base64.
    """
    check_auth(request)
    body = await request.json()
    text = body.get("text")
    voice_name = body.get("voice","en-US-Wavenet-D")
    speaking_rate = float(body.get("speaking_rate", 1.0))
    pitch = float(body.get("pitch", 0.0))
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' in body")
    # Initialize client (relies on Google ADC or env var)
    try:
        client = texttospeech.TextToSpeechClient()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Google TTS client: {e}")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=voice_name.split('-')[0] if '-' in voice_name else 'en-US', name=voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=speaking_rate, pitch=pitch)
    try:
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synth failed: {e}")
    b64 = base64.b64encode(response.audio_content).decode('ascii')
    return JSONResponse({"audio_base64": b64, "encoding": "mp3"})


@app.post("/github/sync")
async def github_sync(request: Request):
    """Basic GitHub sync helper: lists repos accessible by token and returns them. Accepts 'token' in body."""
    check_auth(request)
    body = await request.json()
    token = body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing GitHub token in body.token")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.request(method, url, headers=safe_headers, json=data)
        return JSONResponse({"status_code": r.status_code, "headers": dict(r.headers), "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text})
            r.raise_for_status()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        repos = r.json()
    # Optionally you could sync contents to a local store or trigger webhooks; here we just return the list.
    return JSONResponse({"count": len(repos), "repos": repos})



@app.post("/gcp/load_service_account")
async def gcp_load_service_account(request: Request):
    """Load a JSON service account from Secret Manager and write to a local temp file.
    Body should include: {"secret_name": "projects/PROJECT_ID/secrets/SECRET_NAME"}
    Returns the path where credentials were written and sets GOOGLE_APPLICATION_CREDENTIALS for the process.
    """
    check_auth(request)
    body = await request.json()
    secret_name = body.get("secret_name")
    if not secret_name:
        raise HTTPException(status_code=400, detail="Missing 'secret_name' in body")
    try:
        client = secretmanager.SecretManagerServiceClient()
        # Access the latest version
        name = f"{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to access secret: {e}")
    # write to temp file
    try:
        td = tempfile.mkdtemp(prefix='gcp_sa_')
        p = pathlib.Path(td) / 'service_account.json'
        p.write_text(payload)
        # set environment var for this process
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(p)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write credentials: {e}")
    return JSONResponse({"path": str(p)})



@app.post("/jobs/enqueue")
async def jobs_enqueue(request: Request):
    check_auth(request)
    body = await request.json()
    jtype = body.get("type")
    action = body.get("action")
    payload = body.get("payload", {})
    if not jtype or not action:
        raise HTTPException(status_code=400, detail="Missing 'type' or 'action'")
    q = job_table.insert().values(type=jtype, action=action, payload=json.dumps(payload), status='pending')
    job_id = await database.execute(q)
    return JSONResponse({"job_id": job_id, "status": "queued"})


@app.post("/memory/rehydrate")
async def memory_rehydrate(request: Request):
    """Collect memory items for a namespace and return a concatenated context block suitable for priming a GPT-style model."""
    check_auth(request)
    body = await request.json()
    namespace = body.get("namespace", "default")
    limit = int(body.get("limit", 50))
    q = memory_table.select().where(memory_table.c.namespace == namespace).limit(limit)
    rows = await database.fetch_all(q)
    pieces = []
    for r in rows:
        try:
            val = json.loads(r["value"])
        except Exception:
            val = r["value"]
        pieces.append(f"Key: {r['key']}\nValue: {json.dumps(val)}")
    context = "\n---\n".join(pieces)
    return JSONResponse({"namespace": namespace, "count": len(pieces), "context": context})


@app.post("/gpt/rehydrate")
async def gpt_rehydrate(request: Request):
    """Produce a prompt payload that includes system instruction and rehydrated memory for feeding into a GPT model.
    This does NOT call OpenAI or require an API key; it returns the assembled messages array.
    """
    check_auth(request)
    body = await request.json()
    system = body.get("system", "You are an assistant.")
    namespace = body.get("namespace", "default")
    user_prompt = body.get("prompt", "")
    mem_limit = int(body.get("mem_limit", 50))
    # reuse memory rehydration
    q = memory_table.select().where(memory_table.c.namespace == namespace).limit(mem_limit)
    rows = await database.fetch_all(q)
    memory_texts = []
    for r in rows:
        try:
            val = json.loads(r["value"])
        except Exception:
            val = r["value"]
        memory_texts.append(f"{r['key']}: {json.dumps(val)}")
    memory_block = "\n".join(memory_texts)
    messages = [
        {"role": "system", "content": system},
    ]
    if memory_block:
        messages.append({"role": "system", "content": f"Memory:\n{memory_block}"})
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})
    return JSONResponse({"messages": messages, "namespace": namespace, "memory_count": len(memory_texts)})


 


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/predictions/export")
async def predictions_export():
    """Export all predictions for dashboard"""
    import sqlite3
    conn = sqlite3.connect('mcp_memory.db')
    cur = conn.cursor()
    
    # Get all predictions
    cur.execute("""
        SELECT id, asset, asset_type, prediction_type, timeframe, target_date,
               predicted_value, predicted_direction, confidence, rationale,
               status, outcome, accuracy_score, made_at, resolved_at
        FROM predictions
        ORDER BY made_at DESC
    """)
    
    predictions = []
    for row in cur.fetchall():
        predictions.append({
            'id': row[0],
            'asset': row[1],
            'asset_type': row[2],
            'prediction_type': row[3],
            'timeframe': row[4],
            'target_date': row[5],
            'predicted_value': row[6],
            'predicted_direction': row[7],
            'confidence': row[8],
            'rationale': row[9],
            'status': row[10],
            'outcome': row[11],
            'accuracy_score': row[12],
            'made_at': row[13],
            'resolved_at': row[14]
        })
    
    # Get stats
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
            SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN outcome = 'partial' THEN 1 ELSE 0 END) as partial,
            AVG(CASE WHEN status = 'resolved' THEN accuracy_score ELSE NULL END) as avg_score,
            AVG(confidence) as avg_confidence
        FROM predictions
    """)
    
    row = cur.fetchone()
    total, resolved, correct, partial, avg_score, avg_conf = row
    
    stats = {
        'total_predictions': total or 0,
        'resolved': resolved or 0,
        'pending': (total or 0) - (resolved or 0),
        'correct': correct or 0,
        'partial': partial or 0,
        'accuracy_rate': (correct / resolved * 100) if resolved else 0,
        'avg_accuracy_score': avg_score or 0,
        'avg_confidence': avg_conf or 0
    }
    
    conn.close()
    
    return JSONResponse({
        'predictions': predictions,
        'stats': stats
    })


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/github/repos/create")
async def create_github_repo(request: Request):
    check_auth(request)
    body = await request.json()
    gh_token = body.get("token")
    if not gh_token:
        raise HTTPException(status_code=400, detail="Missing GitHub token in body.token")
    name = body.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing repository name in body.name")
    org = body.get("org")
    private = body.get("private", True)
    headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        if org:
            url = f"https://api.github.com/orgs/{org}/repos"
        else:
            url = "https://api.github.com/user/repos"
        payload = {"name": name, "private": private}
        r = await client.post(url, json=payload, headers=headers)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return JSONResponse(r.json())


@app.get("/github/repos/list")
async def list_github_repos(request: Request, org: str | None = None):
    check_auth(request)
    token = request.headers.get("x-github-token") or request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Provide GitHub token via header 'X-GitHub-Token' or query param 'token'")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        if org:
            url = f"https://api.github.com/orgs/{org}/repos"
        else:
            url = "https://api.github.com/user/repos"
        r = await client.get(url, headers=headers)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return JSONResponse(r.json())


@app.get("/gcloud/projects")
async def gcloud_projects(request: Request):
    check_auth(request)
    token = request.headers.get("x-gcloud-token") or request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Provide GCloud OAuth2 access token via header 'X-GCloud-Token' or query param 'token'")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://cloudresourcemanager.googleapis.com/v1/projects"
        r = await client.get(url, headers=headers)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return JSONResponse(r.json())


@app.post("/cloudrun/services/create")
async def cloudrun_create(request: Request):
    check_auth(request)
    body = await request.json()
    token = body.get("token")
    project = body.get("project")
    region = body.get("region", "us-central1")
    service_id = body.get("service_id")
    service_body = body.get("service")
    if not token or not project or not service_id or not service_body:
        raise HTTPException(status_code=400, detail="Missing required fields: token, project, service_id, service")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"https://run.googleapis.com/v1/projects/{project}/locations/{region}/services?serviceId={service_id}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, json=service_body, headers=headers)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return JSONResponse(r.json())


@app.post("/proxy")
async def proxy(request: Request):
    check_auth(request)
    body = await request.json()
    method = body.get("method", "GET").upper()
    url = body.get("url")
    headers = body.get("headers", {})
    data = body.get("body")
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' in body")
    if method not in ALLOWED_HTTP_METHODS:
        raise HTTPException(status_code=405, detail="Method not allowed")
    await validate_outbound_url(url)
    safe_headers = sanitize_headers(headers or {})
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.request(method, url, headers=safe_headers, json=data)
        return JSONResponse({"status_code": r.status_code, "headers": dict(r.headers), "body": r.json() if r.headers.get("content-type",""").startswith("application/json") else r.text})


@app.post("/scrape")
async def scrape_endpoint(request: Request):
    check_auth(request)
    body = await request.json()
    url = body.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' in body")
    await validate_outbound_url(url)
    try:
        result = await scrape(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # Optionally store to memory
    save = body.get("save", False)
    if save:
        ns = body.get("namespace", "scrapes")
        key = body.get("key") or result["url"]
        query = memory_table.insert().values(namespace=ns, key=key, value=json.dumps({"url": result["url"], "text": result["text"]}))
        await database.execute(query)
    return JSONResponse(result)


# Simple in-memory keyword plugin registry
keyword_plugins = {}


@app.post("/plugins/keywords/add")
async def add_keyword_plugin(request: Request):
    check_auth(request)
    body = await request.json()
    name = body.get("name")
    keywords = body.get("keywords", [])
    action = body.get("action")
    if not name or not keywords or not action:
        raise HTTPException(status_code=400, detail="Missing fields: name, keywords, action")
    keyword_plugins[name] = {"keywords": keywords, "action": action}
    return JSONResponse({"status": "ok", "plugin": name})


@app.get("/plugins/keywords/list")
async def list_keyword_plugins(request: Request):
    check_auth(request)
    return JSONResponse(keyword_plugins)


@app.post("/crawl/enqueue")
async def crawl_enqueue(request: Request):
    check_auth(request)
    body = await request.json()
    start = body.get("start_url")
    max_pages = int(body.get("max_pages", 50))
    max_depth = int(body.get("max_depth", 2))
    start_host = await validate_outbound_url(start) if start else None
    allowed = filter_allowed_domains(body.get("allowed_domains"))
    save = body.get("save", False)
    if not start:
        raise HTTPException(status_code=400, detail="Missing start_url")
    if start_host and start_host not in allowed:
        allowed.append(start_host)
    # Run crawl synchronously here for demo; in production enqueue as background job
    results = await crawl(start, max_pages=max_pages, max_depth=max_depth, allowed_domains=allowed)
    # Optionally store to memory
    if save:
        ns = body.get("namespace", "crawls")
        for r in results:
            key = r["url"]
            q = memory_table.insert().values(namespace=ns, key=key, value=json.dumps({"url": r["url"], "html": r["html"]}))
            await database.execute(q)
    # Run keyword plugins on crawled pages
    matches = []
    for r in results:
        text = r["html"]
        for name, p in keyword_plugins.items():
            for kw in p["keywords"]:
                if kw.lower() in text.lower():
                    matches.append({"url": r["url"], "plugin": name, "keyword": kw, "action": p["action"]})
    return JSONResponse({"count": len(results), "matches": matches})


# ===== UNIFIED ENDPOINTS FOR GATEWAY COMPATIBILITY =====

@app.post("/api/predict")
async def predict_endpoint(asset: str = None, prediction_type: str = "price", confidence: int = 50):
    """Predict endpoint - historical pattern analysis"""
    conn = databases.Database(DB_PATH)
    await conn.connect()
    
    try:
        # Query historical predictions
        query = "SELECT COUNT(*) FROM predictions WHERE status = 'pending'"
        pending_predictions = await conn.fetch_val(query)
        
        return {
            'success': True,
            'asset': asset,
            'prediction_type': prediction_type,
            'confidence': confidence,
            'pending_predictions': pending_predictions,
            'source': 'meta'
        }
    finally:
        await conn.disconnect()


@app.post("/api/crawl")
async def crawl_endpoint(url: str = None, depth: int = 1):
    """Crawl endpoint - metadata and job management"""
    conn = databases.Database(DB_PATH)
    await conn.connect()
    
    try:
        # Create crawl job
        query = """
            INSERT INTO jobs (type, action, payload, status)
            VALUES (:type, :action, :payload, :status)
        """
        values = {
            "type": "crawl",
            "action": "url_crawl",
            "payload": json.dumps({"url": url, "depth": depth}),
            "status": "pending"
        }
        job_id = await conn.execute(query, values)
        
        return {
            'success': True,
            'job_id': job_id,
            'url': url,
            'depth': depth,
            'status': 'queued',
            'source': 'meta'
        }
    finally:
        await conn.disconnect()


@app.post("/api/simulate")
async def simulate_endpoint(scenario: str, parameters: dict = None):
    """Simulate endpoint - scenario job creation"""
    conn = databases.Database(DB_PATH)
    await conn.connect()
    
    try:
        # Create simulation job
        query = """
            INSERT INTO jobs (type, action, payload, status)
            VALUES (:type, :action, :payload, :status)
        """
        values = {
            "type": "simulate",
            "action": scenario,
            "payload": json.dumps(parameters or {}),
            "status": "pending"
        }
        job_id = await conn.execute(query, values)
        
        return {
            'success': True,
            'job_id': job_id,
            'scenario': scenario,
            'status': 'queued',
            'source': 'meta'
        }
    finally:
        await conn.disconnect()


@app.get("/api/read/{resource}")
async def read_endpoint(resource: str):
    """Unified read endpoint"""
    conn = databases.Database(DB_PATH)
    await conn.connect()
    
    try:
        if resource == 'memory':
            query = "SELECT key, value FROM memory LIMIT 100"
            rows = await conn.fetch(query)
            return {"resource": resource, "count": len(rows), "data": rows}
        elif resource == 'jobs':
            query = "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50"
            rows = await conn.fetch(query)
            return {"resource": resource, "count": len(rows), "data": rows}
        elif resource == 'predictions':
            query = "SELECT * FROM predictions WHERE status = 'pending' LIMIT 50"
            rows = await conn.fetch(query)
            return {"resource": resource, "count": len(rows), "data": rows}
        else:
            raise HTTPException(status_code=404, detail=f"Resource {resource} not found")
    finally:
        await conn.disconnect()


@app.post("/api/write/{resource}")
async def write_endpoint(resource: str, payload: dict):
    """Unified write endpoint"""
    conn = databases.Database(DB_PATH)
    await conn.connect()
    
    try:
        if resource == 'memory':
            query = """
                INSERT OR REPLACE INTO memory (key, value)
                VALUES (:key, :value)
            """
            values = {
                "key": payload.get('key'),
                "value": json.dumps(payload.get('value'))
            }
            await conn.execute(query, values)
            return {"success": True, "resource": resource, "key": payload.get('key')}
        else:
            raise HTTPException(status_code=404, detail=f"Resource {resource} not found")
    finally:
        await conn.disconnect()


@app.post("/api/analyze/{resource}")
async def analyze_endpoint(resource: str, payload: dict):
    """Unified analyze endpoint"""
    conn = databases.Database(DB_PATH)
    await conn.connect()
    
    try:
        if resource == 'predictions':
            query = "SELECT COUNT(*) as total, status FROM predictions GROUP BY status"
            rows = await conn.fetch(query)
            return {
                'resource': resource,
                'analysis': {
                    'total_predictions': sum(r['total'] for r in rows),
                    'by_status': {r['status']: r['total'] for r in rows}
                }
            }
        elif resource == 'jobs':
            query = "SELECT COUNT(*) as total, status FROM jobs GROUP BY status"
            rows = await conn.fetch(query)
            return {
                'resource': resource,
                'analysis': {
                    'total_jobs': sum(r['total'] for r in rows),
                    'by_status': {r['status']: r['total'] for r in rows}
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"Resource {resource} not found")
    finally:
        await conn.disconnect()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
