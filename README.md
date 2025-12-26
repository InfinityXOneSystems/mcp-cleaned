# Infinity XOS MCP

This repo contains the Infinity XOS MCP server and the unified dashboards for Trading, Intelligence, and Predictions (SPA).

See the quick system index: [INDEX.md](INDEX.md)

## Authoritative Operation Guide (for demos and local runs)

This section describes exactly how this `mcp` system operates and the locations of key artifacts.

1) Services and how to run
- Gateway (FastAPI): `api_gateway.py` — runs on port `8000` by default.
- Dashboard API: `dashboard_api.py` — port `8001` (UI content at `/dashboard.html`).
- Intelligence API: `intelligence_api.py` — port `8002`.
- Local Proxy (landing pages): `local_proxy.py` — port `8080` (mirrors landing pages and proxies admin routes).

Run example (PowerShell):
```powershell
python api_gateway.py
python dashboard_api.py
python intelligence_api.py
```

2) Memory systems
- Local SQLite: `mcp_memory.db` — local intelligence & job storage (see `scripts/init_db.py` to initialize).
- External memory services (optional): the platform can be configured to use external memory services via `SERVICES` map in `api_gateway.py`.

3) Environment variables and `.env.example`
- Place credentials and configuration in environment variables or a `.env` file. Example file: `.env.example` (below).

4) Credential and account locations (local)
- Google service account JSON: path referenced by `GOOGLE_SERVICE_ACCOUNT_JSON` env var (recommended location: `credentials/service-account.json`).
- GitHub token: `GITHUB_TOKEN` env var.
- OAuth tokens: `GOOGLE_OAUTH_TOKEN` env var.
- Local secrets: `local_secrets/` (gitignored). Use this folder for local credential files used during demos.

5) Admin & Doc Evolution controls
- Admin UI: `http://localhost:8000/admin` — Infinity-Monitor.
- Doc Evolution endpoints:
  - `POST /admin/doc/ingest` {source, metadata}
  - `POST /admin/doc/evolve` {doc_id, strategy}
  - `POST /admin/doc/sync` {target}
  - `GET /admin/doc/mode` — current mode
  - `POST /admin/doc/mode` {mode, path_override} — set mode and optional path

6) URLs and local endpoints
- Gateway UI: `http://localhost:8000/admin`
- Health: `http://localhost:8000/health`
- Dashboard: `http://localhost:8001/`
- Intelligence: `http://localhost:8002/`

7) How to use the index
- The `INDEX.md` is the single-page quick index for demos. Use it for talking points in investor demos.
- For developer operations, consult `docs/BLUEPRINT.md` (architecture) and `docs/MANIFEST.yaml` (component list).

8) Safety and best practices
- Default: `DOC_EV_MODE` = `safe` (no external writes). Change via Admin UI only after review.
- Use `DOC_EV_PATH_OVERRIDE` to point to external doc-evolution code if you want to test live mode — but do not enable `live` without audit.

9) Contact & Handoff
- Dev lead: see `DEVELOPER_HANDOFF.md` for contact details and deployment notes.

---

Below is a minimal environment sample (see `.env.example`)


## Quick Start

**Prerequisites:** Python 3.11+, PowerShell on Windows

**Important:** The database (`mcp_memory.db`) is excluded from Git due to size (472MB). You'll create it locally.

### Setup

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Initialize the database schema (creates empty tables):

```powershell
python -c "import sqlite3; conn = sqlite3.connect('mcp_memory.db'); conn.execute('CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY, key TEXT, value TEXT)'); conn.execute('CREATE TABLE IF NOT EXISTS paper_accounts (id INTEGER PRIMARY KEY, account_name TEXT, account_type TEXT, starting_balance REAL, current_balance REAL, created_at TEXT, updated_at TEXT)'); conn.execute('CREATE TABLE IF NOT EXISTS paper_positions (id INTEGER PRIMARY KEY, account_id INTEGER, asset TEXT, asset_type TEXT, direction TEXT, entry_price REAL, position_size REAL, quantity REAL, opened_at TEXT, status TEXT, entry_reason TEXT)'); conn.execute('CREATE TABLE IF NOT EXISTS paper_trades (id INTEGER PRIMARY KEY)'); conn.execute('CREATE TABLE IF NOT EXISTS paper_snapshots (id INTEGER PRIMARY KEY)'); conn.execute('CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY)'); conn.execute('CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY)'); conn.commit(); conn.close(); print('Database initialized')"
```

Or use the included script:

```powershell
python scripts/init_db.py
```

3. (Optional) Seed intelligence memory with 1,271 crawled sources:

```powershell
python scripts/analyze_intelligence.py
```

4. (Optional) Seed demo trading accounts:

```powershell
python scripts/seed_accounts.py
```

### Run the Platform

- Start Trading Dashboard API (port 8001):

```powershell
python dashboard_api.py
```

- Start Intelligence API (port 8002):

```powershell
python intelligence_api.py
```

- Or use the launcher (starts both and opens browser):

```powershell
.\start_servers.ps1
```

- Open the unified SPA:
  - Trading Dashboard: http://localhost:8001/
  - Intelligence Browser: http://localhost:8002/
  - SPA file: [command_center_spa.html](command_center_spa.html)

## MCP Server

### Standard MCP (Orchestrator Only)

- Run the basic MCP server (stdio):

```powershell
python main.py
```

- Optional: set orchestrator endpoint

```powershell
$env:ORCHESTRATOR_URL = "https://orchestrator-896380409704.us-east1.run.app/execute"
python main.py
```

The basic MCP server exposes a single tool `execute(command, payload)` that forwards to the orchestrator.

### 🌌 Omni-Directional Hub (Full Integration)

The extended MCP creates an **omni-directional AI hub** connecting multiple systems for maximum autonomous capabilities.

- Run the Omni Hub:

```powershell
$env:GITHUB_TOKEN = "your_github_token"
python main_extended.py
```

- Test the hub:

```powershell
python test_omni_hub.py
```

**15 Tools Across 4 Systems:**

🔧 **Orchestrator** (1 tool)
- `execute` - Forward commands to Infinity XOS cloud

🐙 **GitHub** (3 tools)
- `github_create_issue` - Create issues in any repo
- `github_search_code` - Search code across GitHub
- `github_get_file_content` - Fetch file contents

🐳 **Docker** (9 tools)
- `docker_list_containers` - List all containers
- `docker_container_action` - Start/stop/restart/remove
- `docker_run_container` - Launch new containers
- `docker_list_images` - List Docker images
- `docker_pull_image` - Pull from registry
- `docker_container_logs` - View logs
- `docker_container_inspect` - Inspect details
- `docker_list_networks` - List networks
- `docker_list_volumes` - List volumes

🧠 **Local Intelligence** (2 tools)
- `query_intelligence` - Search 1,271 intelligence sources
- `get_portfolio_status` - Get trading portfolio stats

**Prerequisites:**
- Docker Desktop running (for Docker tools)
- mcp_memory.db initialized (for intelligence tools)
- GitHub token set (for GitHub tools)

Both MCP servers are safe to run side-by-side (use different names in MCP clients).

## Custom GPT Attachment

 - The MCP HTTP Adapter exposes MCP tools over HTTP/OpenAPI for Custom GPT-style integrations.
 - Adapter base path: `/mcp` (e.g. `http://<host>/mcp`).
 - OpenAPI spec (attach-ready): `GET /mcp/openapi` or `GET /mcp/schema`.
 - Discovery endpoints:
   - `GET /mcp/health` — adapter health
   - `GET /mcp/tools` — list available tools and metadata
   - `POST /mcp/execute` — execute a tool (body: `{ "tool_name": "...", "arguments": {...} }`)
   - `POST /mcp/execute/{tool_name}` — execute a specific tool by name
 - Security: set `MCP_API_KEY` env var and provide `X-MCP-KEY` header. Default `SAFE_MODE=true` blocks unauthenticated calls.
 - Approval flow: critical operations may return `{ "approval_required": true }` and persist a local memory entry under `data/` for manual approval.

Deploy the adapter with `python -m uvicorn omni_gateway:app --host 0.0.0.0 --port $PORT` for Cloud Run compatibility. Ensure `SAFE_MODE` and `MCP_API_KEY` are set in the environment.
