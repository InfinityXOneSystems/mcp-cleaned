# Infinity XOS MCP

This repo contains the Infinity XOS MCP server and the unified dashboards for Trading, Intelligence, and Predictions (SPA).

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

- Run the MCP server (stdio):

```powershell
python main.py
```

- Optional: set orchestrator endpoint

```powershell
$env:ORCHESTRATOR_URL = "https://orchestrator-896380409704.us-east1.run.app/execute"
python main.py
```

The MCP server exposes a single tool `execute(command, payload)` that forwards to the orchestrator.
