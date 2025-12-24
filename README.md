<<<<<<< HEAD
# MCP\n\nMCP orchestration submodule.
=======
Infinity XOS MCP
================

This MCP provides a stdio-based server by default (see `main.py`). To connect this MCP to OpenAI or other hosted services you need a publicly reachable HTTP(S) endpoint.

Quick options:
- Use `ngrok http 8000` to forward a local HTTP server.
- Deploy a small FastAPI adapter that wraps the MCP and validates an `MCP_API_KEY` bearer token.

Example HTTP adapter (minimal):

1. Install requirements:

```powershell
pip install -r requirements.txt
```

2. Run the example server (create `http_adapter.py` with code below):

```powershell
python http_adapter.py
```

3. Expose `http://localhost:8000` via ngrok or a cloud VM, then configure OpenAI to call your endpoint.

Security notes:
- Always require a bearer token for incoming requests. Set `MCP_API_KEY` in the environment and validate it in the adapter.
- Prefer HTTPS in production.

Infinity XOS MCP
================

This MCP provides a stdio-based server by default (see `main.py`). To connect this MCP to OpenAI or other hosted services you need a publicly reachable HTTP(S) endpoint.

Quick options:
- Use `ngrok http 8000` to forward a local HTTP server.
- Deploy a small FastAPI adapter that wraps the MCP and validates an `MCP_API_KEY` bearer token.

Example HTTP adapter (minimal):

1. Install requirements:

```powershell
pip install -r requirements.txt
```

2. Run the example server (create `http_adapter.py` with code below):

```powershell
python http_adapter.py
```

3. Expose `http://localhost:8000` via ngrok or a cloud VM, then configure OpenAI to call your endpoint.

Security notes:
- Always require a bearer token for incoming requests. Set `MCP_API_KEY` in the environment and validate it in the adapter.
- Prefer HTTPS in production.

Cloud Run deployment
--------------------

1. Build and push the container (replace <PROJECT> and <REGION>):

```bash
gcloud builds submit --tag gcr.io/<PROJECT>/infinity-xos-mcp
```

2. Deploy to Cloud Run:

```bash
gcloud run deploy infinity-xos-mcp \
  --image gcr.io/<PROJECT>/infinity-xos-mcp \
  --platform managed \
  --region <REGION> \
  --allow-unauthenticated=false \
  --set-env-vars MCP_API_KEY="YOUR_SECRET_TOKEN"
```

3. Configure OpenAI or ChatGPT plugin manifest to point at the deployed URL (use HTTPS endpoint returned by Cloud Run).
