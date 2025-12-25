# services/mcp

Path: services/mcp

Snapshots: 1

## README.md snippet:

# MCP

Minimal MCP orchestration submodule for Infinity XOS. This package provides a small FastMCP-based server that exposes an MCP endpoint at `/mcp`.

Run locally:

1. Create a virtualenv and install requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start the MCP server:

```powershell
python server.py
```

Default HTTP endpoint: http://localhost:8080/mcp
# MCP

Minimal MCP orchestration submodule for Infinity XOS. This package provides a small FastMCP-based server that exposes an MCP endpoint at `/mcp` and a simple HTTP adapter for compatibility with local tooling.

Run locally:

1. Create a virtualenv and install requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start the MCP server:

```powershell
python server.py
```

## Files (top-level):
- .git
- auto-docs-sync
- http_adapter.py
- mcp_smoke.py
- MODULE_MANIFEST.yaml
- README.md
- requirements.txt
- ROOM_INDEX.md
- run_local.ps1
- server.py
- __pycache__