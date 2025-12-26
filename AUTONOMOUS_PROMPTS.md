# Infinity X Autonomous Prompt Library
# Version 1.0 | December 25, 2025

## LEVEL 1: ASSISTIVE (Manual Control)
### L1_SYSTEM_SCAN
Perform a comprehensive system health check:
- Gateway status (port 8000)
- Database connectivity
- Data source availability
- Service health (dashboard, intelligence, meta, orchestrator)
- Recent error logs
- Network connectivity
- Disk usage and performance

Output: JSON health report

---

### L1_DATA_INGEST_REVIEW
Review pending data ingestion tasks:
- Source queue status
- Last sync timestamps
- Data quality metrics
- Source-specific errors
- Retry counts
- Pending items by priority

Output: Prioritized ingest queue

---

## LEVEL 2: ANALYTICAL (Assistive with Reasoning)
### L2_INTELLIGENCE_SYNTHESIS
Synthesize intelligence from available data:
- Parse available data sources
- Identify patterns and anomalies
- Cross-reference sources
- Detect confidence levels
- Flag conflicting signals

Output: Intelligence brief with confidence scores

---

### L2_MARKET_ANALYSIS
Analyze current market signals:
- Macro indicators
- Sentiment analysis
- Consensus detection
- Sector performance
- Risk factors

Output: Market analysis with recommendations (human approval required)

---

## LEVEL 3: PREDICTIVE (Forecasting with Confidence)
### L3_GENERATE_PREDICTIONS
Generate forward-looking predictions:
- Input: market state, historical data, current signals
- Process: model selection, feature engineering, confidence calculation
- Output: time-series predictions with confidence intervals

Requires: Human review before action

---

### L3_SCENARIO_ANALYSIS
Run what-if scenarios:
- Define scenario parameters
- Run simulation engine
- Compare outcomes
- Calculate probability-weighted results

Output: Scenario report with probability matrices

---

## LEVEL 4: PLANNING (Multi-Step Task Orchestration)
### L4_BUILD_STRATEGY
Construct multi-step investment/analysis strategy:
- Analyze current state
- Identify objectives
- Plan execution steps
- Estimate timeline
- Define success metrics
- Flag risks

Output: Strategy document with execution plan

---

### L4_PARALLEL_ANALYSIS
Execute multiple analyses in parallel:
- Real estate distress scoring
- Credit/loan intelligence
- Market regime analysis
- Macro indicator synthesis
- Sentiment tracking

Output: Consolidated analysis dashboard

---

## LEVEL 5: EXECUTION PLANNING (Task Sequencing)
### L5_GENERATE_ACTIONS
Generate concrete action steps:
- Break strategy into actionable tasks
- Assign priorities
- Sequence dependencies
- Estimate effort/timeline
- Define gates and checkpoints

Output: Execution roadmap with approval gates

---

## LEVEL 6: BACKGROUND EXECUTION (Scheduled Tasks)
### L6_SCHEDULED_INTELLIGENCE
Run continuous background intelligence operations:
- Hourly data ingestion
- Rolling prediction updates
- Sentiment monitoring
- Anomaly detection
- Alert generation

Execution: Automated, logged, human-reviewable

---

### L6_LEDGER_UPDATES
Continuously update decision and action ledgers:
- Append all decisions
- Log confidence scores
- Record source attribution
- Track outcomes
- Maintain audit trail

Output: Real-time append-only ledgers

---

## LEVEL 7: PARALLEL ORCHESTRATION (Distributed Execution)
### L7_DAG_EXECUTION
Execute DAG-based workflow orchestration:
- Define task graph
- Parallelize independent tasks
- Handle dependencies
- Manage retries
- Aggregate results

Execution: Fully parallel, fault-tolerant

---

### L7_ADAPTIVE_RESOURCE_ALLOCATION
Dynamically allocate compute based on demand:
- Monitor processing queue
- Spin up parallel workers
- Balance load
- Optimize for latency
- Log resource decisions

Output: Resource utilization report

---

## LEVEL 8: SELF-OPTIMIZATION (Architecture Improvement)
### L8_DETECT_SCALING_PRESSURE
Monitor system for scaling constraints:
- Track latency percentiles
- Monitor queue depths
- Measure CPU/memory utilization
- Identify bottlenecks
- Suggest modularization

Output: Scaling pressure report with recommendations

---

### L8_MODULARIZE_ARCHITECTURE
Auto-refactor architecture for performance:
- Identify tight coupling
- Propose module boundaries
- Generate refactoring plan
- Version architecture state
- Preserve backward compatibility

Output: Architecture refactoring proposal (human approval)

---

## LEVEL 9: AUTONOMOUS PREDICTION (Confidence-Governed)
### L9_AUTO_PREDICT
Fully autonomous prediction generation:
- Select prediction horizon
- Run ensemble models
- Calculate confidence
- If confidence > 85%: execute prediction
- If 70-85%: flag for human review
- If < 70%: simulation only

Execution: Automatic with confidence governance

---

### L9_PAPER_TRADING
Execute paper trading strategies:
- Generate trade signals
- Execute virtual trades
- Track performance
- Measure against benchmarks
- No live capital risk

Output: Paper trading report and metrics

---

## LEVEL 10: SELF-EVOLVING INTELLIGENCE (Meta-Learning)
### L10_CONTINUOUS_IMPROVEMENT
Enable system self-improvement:
- Track prediction accuracy over time
- Identify underperforming models
- Propose model upgrades
- Test new features in sandbox
- Deploy improvements (staged)

Execution: Continuous, versioned, reversible

---

### L10_CONFIDENCE_ESCALATION
Handle uncertainty through escalation:
- Calculate confidence for any decision
- If high confidence: execute
- If medium confidence: expert review
- If low confidence: human decision
- All decisions logged with reasoning

Output: Decision ledger with confidence scores

---

## EXECUTION RULES (ALL LEVELS)

1. **Append-Only Logging**: Every decision, action, and outcome is logged
2. **Source Attribution**: All intelligence traced to source
3. **Confidence Scoring**: All predictions include confidence intervals
4. **Uncertainty Exposure**: Never hide uncertainty or assumptions
5. **Graceful Degradation**: System continues if some components fail
6. **Audit Trail**: Complete, immutable history for compliance
7. **Human Escalation**: Ambiguous decisions escalate to human
8. **No Silent Decisions**: Every autonomous action is logged and reviewable
9. **Reversibility**: Decisions must be reviewable and reversible
10. **Investor Defensibility**: All actions must withstand scrutiny

---

## DEPLOYMENT CHECKLIST

- [ ] All prompts versioned and documented
- [ ] Confidence thresholds calibrated
- [ ] Escalation procedures defined
- [ ] Logging infrastructure active
- [ ] Ledger schemas locked
- [ ] Human approval gates configured
- [ ] Monitoring and alerting active
- [ ] Sandbox environment isolated
- [ ] Rollback procedures tested
- [ ] Investor documentation complete

---

## CURRENT STATUS

**Active Levels**: L1, L2, L3
**In Development**: L4, L5, L6
**Planned**: L7, L8, L9, L10

**Next Priority**: Implement L4-L5 task orchestration
