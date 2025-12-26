# Intelligence Cockpit — Quick Start

Install requirements:
```powershell
python -m pip install -r requirements.txt
```

Run agents (dev):
```powershell
python -m agents.runner --start
```

Start remote control server (local):
```powershell
python remote_control/server.py
```

Start FastAPI gateway for local testing (do not run in prod directly):
```powershell
python omni_gateway.py
```

Open demo UI: `http://localhost:8000/demo/authority.html`

## Approval flow (governance)

This repository includes a governance layer to gate high-confidence actions and decision endpoints.

Endpoints and categories:
- Read-only: `/v1/intelligence/arrival`, `/v1/intelligence/mirror-business`, `/v1/system/live-map`
- Gated (confidence checked): `/v1/intelligence/pipeline-shadow` (estimates) — not actioning
- Approval-required: `/v1/intelligence/conviction` (if caller role lacks `can_execute` or confidence below threshold, a memory document is written with `requires_approval=true`)

Approval endpoint:
- `POST /v1/orchestrator/approve` with body `{ memory_id, decision_type, approved_by, approval_level }` updates the memory document and marks `approval_status` as `approved`.

Behavior rules:
- System remains in DRY-RUN mode; no external actions will be executed until approval is granted and the orchestrator is explicitly enabled.
- Governance checks use `governance.is_action_allowed(confidence, requires_high_trust)` and `permission_from_role(role)`.

