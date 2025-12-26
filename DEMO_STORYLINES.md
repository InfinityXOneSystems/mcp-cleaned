# Demo Storylines (Investor-Grade)

Purpose: make power tangible without changing enforcement. Each storyline stays demo-safe.

## 1) Distressed SMB Radar (30-day Outlook)
- Setup: Select industries = [smb_distress], sources = [news, filings], demo_safe = true
- Flow: Scout discovers filings + negative PR → Extractor structuring → Predictor outputs distress probabilities → Ranker surfaces top 25
- Visuals: Forecast with band; driver bars; lead list with confidence
- Narrative: “Over the last 14 days… predicted distress 0.64 at 81% confidence… action: outreach within 48h.”

## 2) Energy Deal Forecaster (90-day Conversion)
- Setup: industries = [energy], sources = [news, web]
- Flow: Scout grid/load + procurement delays → Features → Predictor → Ranker
- Visuals: 90-day forecast; lead score distribution
- Narrative: “Conversion likelihood +37% over baseline; drivers: outage trends, permitting backlog.”

## 3) Competitive Talent Drain Detector (60-day Risk)
- Setup: industries = [technology], sources = [job_postings, forums, news]
- Flow: Hiring delta + exec departures → Predictor churn risk → Top accounts for win-back
- Visuals: Driver contributions; account risk table
- Narrative: “Attrition signals elevated; 45% churn risk at 69% confidence; prioritize win-back.”
