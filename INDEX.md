# MCP System Index (Omni Hub)

This index is the authoritative, investor-ready summary for the local `mcp` system. It is intentionally minimal and focused for quick handoff and demo runs.

## Purpose
- Provide a single-page index for the `mcp` system used during investor demos.
- Document key endpoints, run steps, and the admin controls (Doc Evolution safety toggle).

## Quick Start (60s)
- Install: `pip install -r requirements.txt`
- Initialize DB: `python scripts/init_db.py` (or see README.md for manual SQL)
- Start gateway: `python api_gateway.py` (default port 8000)
- Open admin UI: `http://localhost:8000/admin` (Infinity-Monitor / Admin Console)

## Key Endpoints
- `/health` - Gateway health
- `/predict` - Unified predict API
- `/crawl` - Unified crawl API
- `/simulate` - Simulation/backtest API
- `/admin` - Admin Console (UI)
- `/admin/doc/ingest` - Ingest a document (admin)
- `/admin/doc/evolve` - Evolve a document (admin)
- `/admin/doc/sync` - Sync documents (admin)
- `/admin/doc/mode` - Get/set Doc Evolution mode (safe/read-only/live)

## Admin Notes
- Doc Evolution integration defaults to `safe` mode to prevent unintended external writes. Use the Admin Console toggle (`Settings → Doc Evolution Controls`) to change to `read-only` or `live`.
- Audit all admin doc operations. Use `REI__System_Audit_Log` (ledger) for permanent records.

## Why this repo is self-sustaining
- The `mcp` repo includes a FastAPI gateway, admin UI, local proxy for landing pages, crawler, and integrations which allow it to run independently of external submodules.
- Use `DOC_EV_MODE` environment variable to control behavior when connecting to external doc systems.

## Next Steps (for sync with infinity-xos)
1. Run read-only consolidation of `infinity-xos` `system_index/docs_index.json` to collect per-subsystem summaries.
2. Review the staging summaries, then open a PR on `infinity-xos` to merge authoritative changes.
3. Enable `DOC_EV_MODE=live` only after audits and human approval.

---

Generated and managed by the Omni Hub administration tools.
