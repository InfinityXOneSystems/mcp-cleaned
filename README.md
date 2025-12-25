# Infinity XOS MCP

This repo contains the Infinity XOS MCP server and the unified dashboards for Trading, Intelligence, and Predictions (SPA).

## Quick Start

- Prereqs: Python 3.11+, PowerShell on Windows
- Install deps:

```powershell
pip install -r requirements.txt
```

- Seed intelligence memory (optional, builds categories and sources):

```powershell
python scripts/analyze_intelligence.py
```

- Start Trading Dashboard API (port 8001):

```powershell
python dashboard_api.py
```

- Start Intelligence API (port 8002):

```powershell
python intelligence_api.py
```

- Open the unified SPA:
	- Trading SPA (served): http://localhost:8001/
	- Intelligence Browser: http://localhost:8002/
	- SPA file (direct): command_center_spa.html

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
