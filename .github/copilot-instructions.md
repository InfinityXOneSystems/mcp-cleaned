## Copilot Instructions — Infinity X Autonomous Intelligence Cockpit

You are an AI coding agent working inside this repository. The goal is to maintain and extend an autonomous intelligence cockpit composed of a FastAPI gateway (`omni_gateway.py`), agents (`agents/`), rehydrate tooling, memory (Firestore), and a demo/FE. Follow these project-specific rules:

1. Big picture
- `omni_gateway.py` is the main HTTP entrypoint. It mounts intelligence routes from `intelligence_endpoints.py` and serves the cockpit UI files like `cockpit.html` and `webview/dashboard.html`.
- Memory is persisted to Firestore (`mcp_memory` collection). `init_firestore()` in `omni_gateway.py` is used across scripts.
- Agent scaffolding lives in `agents/` and is launched via `python -m agents.runner --start`.

2. When adding endpoints
- Validate inputs with Pydantic models placed next to endpoints (see `intelligence_endpoints.py`).
- Persist any inference to Firestore following the `mcp_memory` schema: include `session_hash`, `type`, `content`, `confidence`, `sources`, `prompt_hash`, `created_at`.
- Use heuristics-first; only call external LLMs through a pluggable adapter. Do not embed keys in code—read `OPENAI_API_KEY` from env.

3. Agent behavior
- Agents are cooperative but isolated: implement as `async def run(cfg)` and they should never block indefinitely. Use small sleep loops and yield periodically.
- Agents must write status updates into `mcp_memory` with type `agent_status` every run cycle.

4. Security and ops
- Do not commit service account JSON or secrets. Use `GOOGLE_APPLICATION_CREDENTIALS` for local runs and Workload Identity on Cloud Run.
- Remote control server is `remote_control/server.py`. It requires `REMOTE_CTRL_TOKEN` as `Authorization: Bearer <token>` header for commands. Only add safe command mappings to `allowed` dictionary.

5. Demo and UI
- Demo files live in `demo/` and `webview/`. UI should play TTS using the `spoken` field returned by endpoints.

6. Tests & local dev
- Run `python -m agents.runner --start` to simulate background agents.
- Use `python remote_control/server.py` to run the local command bridge (binds to 127.0.0.1:8765 by default).

7. Repo patterns
- Add new prompt templates under `schemas/prompts/` with metadata including `id`, `description`, `system_prompt`, and `temperature`.
- Use `rehydrate_master.py` to produce canonical manifests and to persist boot-time instructions into Firestore.

8. When modifying core systems
- If changing `init_firestore()` or `mcp_memory` layout, update `inspect_firestore.py`, `rehydrate_master.py`, and any agent that reads memory.
- Backwards-compatible migrations only; prefer `merge=True` when writing docs.

Examples
- Add an endpoint: Create `schemas/your_schema.json`, add Pydantic model in endpoint file, persist memory via `write_memory()` helper in `intelligence_endpoints.py`.

If you need clarification on an integration (Cloud Run, Firestore rules, or secret management), ask for the environment variables you have available and whether to use Workload Identity.
