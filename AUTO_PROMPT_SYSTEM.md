# Auto Prompt / Brain Factory System (Operator Spec)

Objective: define a durable prompt registry with versioning, chain orchestration, testing, and evolution — without touching auth or entrypoints.

## Registry Model
- Each prompt is immutable per version (`id@version`).
- Versions use semver (`major.minor.patch`).
- Rollback = change the active pointer to an older version; artifacts remain immutable.
- Metadata fields: `tags[]`, `owner`, `changelog[]`, `created_at`, `updated_at`.

## Prompt → Agent → Tool Chains
- Chain step:
```json
{
  "prompt_ref": "lead-scout@1.0.0",
  "agent_role": "scout|executor|predictor|memory|architect",
  "tools": ["github_search_code", "web_fetch"],
  "inputs": {"vars": ["session_hash","industry"]},
  "outputs": {"expects": ["artifacts","insights"]},
  "success_criteria": ["artifacts.length >= 10"]
}
```
- Chains are acyclic; steps can emit handoff envelopes to the next role.

## Testing & Simulation
- Golden tests: fixed inputs → expected substrings or structured fields; record drift over time.
- Sandbox mode: run chains with synthetic docs and freeze tool responses.
- Metrics: coverage (branches exercised), stability (pass rate), and regression deltas.

## Evolution Strategy
- Shadow evaluation: deploy `minor` versions behind the scenes and compare metrics.
- Promotion rules: require test pass, regression ≤ threshold, and operator signoff.
- Deprecation: mark `deprecated_at`; block as a policy (auditor-controlled).

## Storage
- Store prompt definitions under `schemas/prompts/` alongside YAML schema.
- Persist registry index to Firestore if needed (docs only; auditors to harden lifecycle controls).
