# AGENT DESIGN PRINCIPLES

## All Agents Must

- Have a clear purpose
- Be name-scoped
- Operate independently
- Report observable outputs
- Be replaceable

## Agent Categories

- **Scrapers** — Data collection
- **Analysts** — Pattern recognition
- **Validators** — Quality assurance
- **Builders** — Infrastructure creation
- **Monitors** — Health surveillance

## Agents May

- Run in parallel
- Schedule themselves
- Trigger other agents
- Improve system reliability

## Agents Must Never

- Drift from purpose
- Execute CRITICAL actions without approval
- Operate without logging
