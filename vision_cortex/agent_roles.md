# Agent Roles

| Role | Purpose | Inputs | Outputs | Governance |
| --- | --- | --- | --- | --- |
| Crawler | Gather external signals | Seed sources | Observations | LOW |
| Ingestor | Clean, normalize, embed | Observations | Cleaned docs + embeddings | LOW |
| Organizer | Cluster knowledge | Cleaned docs | Thematic clusters | LOW |
| Predictor | Forecast scenarios | Clusters | Predictions with horizons | MEDIUM |
| Visionary | Imagine futures | Predictions | Hypothetical scenarios | MEDIUM |
| Strategist | Backcast plans | Scenarios + predictions | Plan steps | MEDIUM |
| CEO | Prioritize actions | Plan steps | Ranked actions | HIGH |
| Validator | Stress-test outputs | Predictions/scenarios | Risks, contradictions | HIGH |
| Documentor | Human-facing summaries | Predictions/steps/actions | Reports | LOW |
| Evolver | Propose improvements & retire/spawn agents | Validation, metrics, contradictions | Evolution suggestions | HIGH |

All agents log to the message bus, persist to memory when configured, and respect governance escalation (default UP if unclear).
