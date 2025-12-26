# Prediction & Intelligence Model (Operator Spec)

Purpose: define a sellable intelligence layer with clear contracts. No enforcement, no secret handling.

## Signal → Feature → Prediction → Outcome
- Signal: observable event or pattern from crawlers, integrations, or ops (e.g., layoffs spike, delinquency rumor).
- Feature: engineered variable derived from signals (e.g., 7d headline velocity, hiring delta, liquidity proxy).
- Prediction: model output over a horizon (e.g., lead conversion likelihood, distress probability).
- Confidence: band or score representing epistemic/aleatoric uncertainty.
- Outcome: recommended action with rationale and expected impact.

## Collections (Firestore; docs only)
### `signals`
- Key: `signal_id`
- Fields: `entity_id`, `name`, `strength (0-1)`, `source`, `industry_tags[]`, `ts`, `session_hash`, `payload`

### `features`
- Key: `feature_id`
- Fields: `entity_id`, `vector` (map of `name:value`), `window` (e.g., `7d`), `ts`, `session_hash`, `provenance[]`

### `predictions`
- Key: `prediction_id`
- Fields:
  - `entity_id`, `horizon_days`, `model_id`, `ts`
  - `predicted` (number or class), `confidence` (0–1)
  - `band` (object: `lower`, `upper`) when time-series
  - `drivers[]` (top SHAP-like contributions or heuristic factors)
  - `lead_score` (0–100)
  - `recommendations[]` (actions with rationale)
  - `session_hash`, `provenance[]`

## Lead Scoring (Reference Logic)
```
lead_score = round(100 * sigmoid(
  w1*distress_prob + w2*intent_prob + w3*fit_score + w4*recency
))
```
- Calibrate `w*` via validation; default monotonic constraints preferred.
- Clamp to [0, 100]; log calibration metadata in `predictions.provenance`.

## Time-Series Forecasting (Conceptual)
- Models: ETS/Prophet-like seasonal baselines, gradient boosting regressors, or small linear baselines as fallbacks.
- Horizons: 7/30/90 days with per-horizon confidence bands.
- Aggregations: by industry, region, or account tier.

## Confidence Band Modeling
- Provide `lower`/`upper` per horizon.
- Report band width; flag low-confidence states for “human-in-the-loop” suggestions.

## Industry Views (Examples)
- Energy: supply chain disruptions → pricing risk → conversion odds for service firms.
- SMB Distress: legal filings + negative PR velocity → distress probability.
- Real Estate: vacancy + rates + permitting delays → time-to-lease predictions.

## Recommended Action Templates
- “Outreach within 48h; reference [driver]; offer [playbook]”
- “Defer engagement; confidence band wide; request additional signals.”
