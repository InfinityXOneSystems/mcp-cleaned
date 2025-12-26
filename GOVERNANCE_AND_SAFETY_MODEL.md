# GOVERNANCE MODEL

All actions are classified into governance levels:

## LOW
- Read-only
- Analysis
- Reporting
- Recommendations

## MEDIUM
- Code generation
- Configuration changes
- Non-destructive automation

## HIGH
- Resource creation
- Deployments
- External communications
- Data writes

## CRITICAL
- Credential changes
- Deletions
- Irreversible actions
- Financial or legal impact

## Rules

- **SAFE_MODE** is always enabled
- **CRITICAL** actions require explicit confirmation
- All executions must be explainable
- Every action must log intent, result, and follow-up checks

## Default Behavior

If governance is unclear, default **UP** (never down).
