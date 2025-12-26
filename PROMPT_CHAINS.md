# Example Enterprise Prompt Chains

This file shows how to compose prompts into agent/tool chains without changing enforcement.

## Lead Sniper Chain v1
```json
{
  "chain_id": "lead-sniper-v1",
  "steps": [
    {
      "prompt_ref": "lead-scout@1.0.0",
      "agent_role": "scout",
      "tools": ["web_fetch","news_search"],
      "inputs": {"vars": ["session_hash","industry","geo"]}
    },
    {
      "prompt_ref": "lead-extract@1.0.0",
      "agent_role": "executor",
      "tools": ["dom_extract","llm_extract"],
      "inputs": {"vars": ["artifact_refs"]}
    },
    {
      "prompt_ref": "lead-predict@1.0.0",
      "agent_role": "predictor",
      "tools": ["feature_engineer","timeseries_forecast"],
      "inputs": {"vars": ["entity_features"]}
    },
    {
      "prompt_ref": "lead-rank@1.0.0",
      "agent_role": "architect",
      "tools": ["rank_score"],
      "inputs": {"vars": ["predictions"]}
    },
    {
      "prompt_ref": "lead-report@1.0.0",
      "agent_role": "memory",
      "tools": ["narrative_render","vega_render"],
      "inputs": {"vars": ["top_leads","graphs"]}
    }
  ]
}
```

## Notes
- Each step references a `prompt_ref` conforming to `PROMPT_SCHEMA.yaml`.
- Chains are declarative and audited separately; execution is builder-implemented.
