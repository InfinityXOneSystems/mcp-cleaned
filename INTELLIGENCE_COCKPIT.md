# Intelligence Cockpit — Workspace Guide

This folder contains scaffolding and configuration to transform this repository into an autonomous intelligence cockpit inside VS Code.

Contents
- `agents/` — agent scaffolding (Python) for background workers
- `remote_control/` — FastAPI server to receive secure remote commands
- `webview/` — dashboard webview assets (HTML/CSS/JS)
- `vscode/` — recommended VS Code settings, extensions list, and theme stub
- `schemas/` — prompt templates and JSON schemas

Quick start
1. Install recommended VS Code extensions (see `vscode/extensions.txt`).
2. Ensure `GOOGLE_APPLICATION_CREDENTIALS` and `FIRESTORE_PROJECT` envs are set for Firestore integration.
3. Run `python -m agents.runner --start` to start background agents (local dev).
4. Start remote-control server: `python remote_control/server.py` (binds to 127.0.0.1 by default, see `--public` option).

Security note: Do not expose the remote-control endpoint without a reverse-proxy and token-based auth.
