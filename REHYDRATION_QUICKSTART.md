# INFINITY X INTELLIGENCE — REHYDRATION QUICKSTART

## 🚀 EXECUTE REHYDRATION SEQUENCE

### Option 1: Full Automated Rehydration (Recommended)

```powershell
# Set environment variables
$env:GATEWAY_URL = "https://gateway.infinityxoneintelligence.com"
$env:MCP_API_KEY = "INVESTORS-DEMO-KEY-2025"
$env:SAFE_MODE = "true"

# Execute full rehydration
python rehydrate_executor.py full
```

### Option 2: Health Check Only

```powershell
# Quick health verification
python rehydrate_executor.py health
```

### Option 3: Start Continuous Monitor

```powershell
# Start continuous monitoring loop (runs indefinitely)
$env:LOOP_INTERVAL = "60"  # seconds between cycles
python continuous_monitor.py
```

---

## 📋 REHYDRATION PHASES

The rehydration executor performs these phases:

1. **Gateway Verification**
   - Check `/health`, `/autonomy/health`, `/langchain/health`
   - Verify MCP tools inventory (135+ tools)
   - Validate governance levels

2. **Memory Initialization**
   - Connect to Firestore (`mcp_memory` collection)
   - Query recent system state
   - Persist boot event

3. **Cortex Layer Activation**
   - Initialize Vision Cortex (strategic intelligence)
   - Initialize Execution Cortex (MCP orchestration)
   - Initialize Validator Cortex (governance enforcement)
   - Initialize Memory Cortex (Firestore persistence)
   - Initialize Agent Swarm Layer

4. **Genesis Agent Creation**
   - 🛡️ Sentinel (health monitoring, 5m interval)
   - 🧱 Constructor (build/deploy, 15m interval)
   - 🔮 Oracle (predictions, 60m interval)
   - 📜 Archivist (memory persistence, 30m interval)

5. **Continuous Loop Initialization**
   - Start 60s monitoring cycle
   - Tasks: health checks, signal processing, task execution, metrics, state persistence

---

## 🔧 CONFIGURATION

### Environment Variables

```bash
# Required
GATEWAY_URL=https://gateway.infinityxoneintelligence.com
MCP_API_KEY=INVESTORS-DEMO-KEY-2025

# Optional
SAFE_MODE=true                    # DRY_RUN mode for CRITICAL operations
LOOP_INTERVAL=60                  # Continuous monitor cycle interval (seconds)
FIRESTORE_PROJECT=infinity-x-one-systems
FIRESTORE_COLLECTION=mcp_memory
```

### Local Development

```bash
# Use local gateway
GATEWAY_URL=http://127.0.0.1:8000
```

---

## 📊 MONITORING

### View Real-time Logs

The rehydration executor and continuous monitor output structured logs:

```
[2025-12-26T12:00:00.000000] [Cycle 1] [INFO] ═══ Cycle 1 Start ═══
[2025-12-26T12:00:00.500000] [Cycle 1] [INFO] ✅ System health: OK
[2025-12-26T12:00:01.000000] [Cycle 1] [INFO] 📡 Processed 5 signals
[2025-12-26T12:00:01.500000] [Cycle 1] [INFO] ⚙️ Executed 3 tasks
[2025-12-26T12:00:02.000000] [Cycle 1] [INFO] ═══ Cycle 1 Complete ═══
```

### Query System State

```powershell
# Query recent memory via gateway
curl "https://gateway.infinityxoneintelligence.com/memory/query?type=system&limit=10" `
  -H "X-MCP-KEY: INVESTORS-DEMO-KEY-2025"
```

### Check Agent Status

```powershell
# List all agents
curl "https://gateway.infinityxoneintelligence.com/agents/list" `
  -H "X-MCP-KEY: INVESTORS-DEMO-KEY-2025"
```

---

## 🛡️ SAFE MODE

When `SAFE_MODE=true`:
- CRITICAL operations require explicit confirmation
- Agent creation runs in DRY_RUN mode
- All operations are validated before execution
- Full audit trail persisted to Firestore

When `SAFE_MODE=false`:
- LIVE execution for all operations
- Agents immediately active
- **Use with caution in production**

---

## 🔄 CONTINUOUS OPERATION

The continuous monitor runs indefinitely with these tasks every cycle:

1. **check_system_health()** - Verify all health endpoints
2. **process_new_signals()** - Query and act on high-confidence signals
3. **execute_pending_tasks()** - Execute queued agent tasks
4. **detect_anomalies()** - Identify system issues (errors, agent failures)
5. **update_metrics()** - Track performance metrics
6. **persist_state()** - Save system snapshot every 10 cycles

### Stop Monitor

```
Press Ctrl+C to gracefully shutdown
```

The monitor will persist final state before exiting.

---

## 🧪 EXAMPLE OUTPUT

```
╔══════════════════════════════════════════════════════════╗
║   INFINITY X INTELLIGENCE — REHYDRATION EXECUTOR v1.0    ║
╚══════════════════════════════════════════════════════════╝

Session Hash: a1b2c3d4e5f6g7h8
Gateway: https://gateway.infinityxoneintelligence.com
Safe Mode: true
Boot Time: 2025-12-26T12:00:00.000000

═══ PHASE 1: GATEWAY VERIFICATION ═══
Checking /health...
✅ Gateway operational: {'status': 'success', 'uptime': 86400}
Checking /autonomy/health...
✅ Autonomy system: operational
Checking /langchain/health...
✅ LangChain system: operational
Checking /mcp/tools...
✅ MCP Tools available: 135
   Governance: LOW=45, MEDIUM=52, HIGH=28, CRITICAL=10

═══ PHASE 2: MEMORY INITIALIZATION ═══
Querying recent system state...
✅ Memory system connected
   Retrieved 5 recent entries
Persisting boot event to memory...
✅ Boot event persisted

═══ PHASE 3: CORTEX LAYER ACTIVATION ═══
   vision_cortex: initializing
   execution_cortex: live
   validator_cortex: live
   memory_cortex: live
   agent_swarm: standby
✅ All cortex layers initialized

═══ PHASE 4: AGENT GENESIS ═══
Creating agent: 🛡️ Sentinel
   ✅ 🛡️ Sentinel activated
Creating agent: 🧱 Constructor
   ✅ 🧱 Constructor activated
Creating agent: 🔮 Oracle
   ✅ 🔮 Oracle activated
Creating agent: 📜 Archivist
   ✅ 📜 Archivist activated

═══ PHASE 5: CONTINUOUS LOOP INITIALIZATION ═══
Loop interval: 60s
Tasks: check_system_health, process_new_signals, execute_pending_tasks, update_metrics, persist_state
✅ Continuous loop initialized
   Note: Loop will run in background via agent orchestrator

╔══════════════════════════════════════════════════════════╗
║                  REHYDRATION COMPLETE                    ║
╚══════════════════════════════════════════════════════════╝

Gateway Reachable: ✅
Memory Connected: ✅
Cortex Layers: 5 initialized
Agents Active: 4
Errors: None

🚀 System Status: OPERATIONAL
✨ Intelligence layers ready for autonomous operation
```

---

## 🎯 NEXT STEPS

After rehydration:

1. **Start Continuous Monitor**
   ```powershell
   python continuous_monitor.py
   ```

2. **Access Intelligence Cockpit**
   ```
   https://gateway.infinityxoneintelligence.com/
   ```

3. **Query System Memory**
   ```powershell
   curl "https://gateway.infinityxoneintelligence.com/memory/query?type=insight&limit=20" `
     -H "X-MCP-KEY: INVESTORS-DEMO-KEY-2025"
   ```

4. **Execute Strategic Reasoning**
   ```powershell
   curl -X POST "https://gateway.infinityxoneintelligence.com/intelligence/think" `
     -H "X-MCP-KEY: INVESTORS-DEMO-KEY-2025" `
     -H "Content-Type: application/json" `
     -d '{"objective":"Analyze system health and identify optimization opportunities","reasoning_depth":7}'
   ```

---

## 📞 SUPPORT

- **Documentation**: See [CUSTOM_GPT_REHYDRATE.md](./CUSTOM_GPT_REHYDRATE.md)
- **Repository**: https://github.com/InfinityXOne/mcp
- **Gateway**: https://gateway.infinityxoneintelligence.com

---

**✅ SYSTEM READY FOR ALPHA–OMEGA PROTOCOL EXECUTION**

**BEGIN.**
