# Safety & Governance

- Governance levels: LOW, MEDIUM, HIGH, CRITICAL (default UP if unclear).
- SAFE_MODE always enforced; CRITICAL requires explicit human confirmation.
- All actions log intent, result, follow-up checks with timestamps and agent identity.
- Validator agent monitors contradictions, scenario uncertainty, and policy adherence.
- Router enforces governance before dispatch; memory keeps audit trail in `mcp_memory`.
- Observability: structured logs on bus, metrics (latency, success, dissent ratio), memory traces.
