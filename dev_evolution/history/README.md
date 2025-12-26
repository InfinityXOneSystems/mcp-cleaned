# Dev Evolution History

This directory stores immutable planning and decision history for the MCP system.

## Structure

```
history/
├── planning/           # Architecture blueprints and planning metadata
├── decisions/          # Decision records with rationale
├── mutations/          # System mutation proposals and outcomes
├── validations/        # Validation reports and signatures
└── rollbacks/          # Rollback operations and snapshots
```

## Rules

1. **Append-only** — History entries are never modified or deleted
2. **Hash-chained** — Each entry references the previous entry's hash
3. **Validator-signed** — Critical entries require validator signature
4. **Timestamped** — All entries include UTC timestamp

## Entry Schema

```json
{
  "id": "history-<uuid>",
  "timestamp": "ISO-8601",
  "type": "planning|decision|mutation|validation|rollback",
  "agent": "<agent-id>",
  "parent_hash": "<sha256>",
  "content": {},
  "validator_signature": "pending|<signature>",
  "governance_level": "LOW|MEDIUM|HIGH|CRITICAL"
}
```

## Integration

The Recorder Agent (`builder.recorder`) is responsible for writing to this directory.
The Guardian Agent (`builder.guardian`) signs critical entries.
