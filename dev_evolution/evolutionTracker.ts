/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: dev.evolution
 * Validator: pending
 * 
 * Dev Evolution Tracker
 * Responsibilities:
 *   • Record every build and prediction cycle with timestamp.
 *   • Compute deltas between runs (performance, confidence).
 *   • Write JSON logs to mcp/dev_evolution/history/.
 *   • Expose functions recordRun(ctx), compareRuns(idA,idB).
 *   • No network I/O beyond local file writes.
 */

import fs from "fs";
import path from "path";

const HISTORY_DIR = path.resolve(__dirname, "history");

export interface RunRecord {
  id: string;
  timestamp: string;
  type: "build" | "prediction" | "evolution" | "validation";
  agents: string[];
  duration_ms: number;
  confidence: number;
  status: "success" | "partial" | "failed";
  metrics: {
    signals_processed?: number;
    decisions_made?: number;
    files_generated?: number;
    errors?: number;
    warnings?: number;
  };
  context?: Record<string, any>;
}

export interface RunDelta {
  run_a: string;
  run_b: string;
  timestamp: string;
  confidence_delta: number;
  duration_delta_ms: number;
  performance_change: "improved" | "degraded" | "stable";
  metric_deltas: Record<string, number>;
}

// Ensure history directory exists
function ensureHistoryDir(): void {
  if (!fs.existsSync(HISTORY_DIR)) {
    fs.mkdirSync(HISTORY_DIR, { recursive: true });
  }
}

// Generate unique run ID
function generateRunId(type: RunRecord["type"]): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `${type}-${timestamp}-${random}`;
}

// Get all run records
export function getAllRuns(): RunRecord[] {
  ensureHistoryDir();
  const indexPath = path.join(HISTORY_DIR, "index.json");
  
  if (!fs.existsSync(indexPath)) {
    return [];
  }
  
  try {
    const content = fs.readFileSync(indexPath, "utf-8");
    return JSON.parse(content);
  } catch {
    return [];
  }
}

// Save run index
function saveRunIndex(runs: RunRecord[]): void {
  ensureHistoryDir();
  const indexPath = path.join(HISTORY_DIR, "index.json");
  fs.writeFileSync(indexPath, JSON.stringify(runs, null, 2));
}

// Record a new run
export function recordRun(ctx: {
  type: RunRecord["type"];
  agents: string[];
  duration_ms: number;
  confidence: number;
  status: RunRecord["status"];
  metrics?: RunRecord["metrics"];
  context?: Record<string, any>;
}): RunRecord {
  ensureHistoryDir();
  
  const record: RunRecord = {
    id: generateRunId(ctx.type),
    timestamp: new Date().toISOString(),
    type: ctx.type,
    agents: ctx.agents,
    duration_ms: ctx.duration_ms,
    confidence: ctx.confidence,
    status: ctx.status,
    metrics: ctx.metrics || {},
    context: ctx.context
  };
  
  // Save individual run file
  const runPath = path.join(HISTORY_DIR, `${record.id}.json`);
  fs.writeFileSync(runPath, JSON.stringify(record, null, 2));
  
  // Update index
  const runs = getAllRuns();
  runs.push(record);
  saveRunIndex(runs);
  
  console.log(`📊 Evolution: Recorded run ${record.id}`);
  return record;
}

// Get a specific run by ID
export function getRun(id: string): RunRecord | null {
  ensureHistoryDir();
  const runPath = path.join(HISTORY_DIR, `${id}.json`);
  
  if (!fs.existsSync(runPath)) {
    return null;
  }
  
  try {
    const content = fs.readFileSync(runPath, "utf-8");
    return JSON.parse(content);
  } catch {
    return null;
  }
}

// Compare two runs and compute deltas
export function compareRuns(idA: string, idB: string): RunDelta | null {
  const runA = getRun(idA);
  const runB = getRun(idB);
  
  if (!runA || !runB) {
    console.error("❌ One or both runs not found");
    return null;
  }
  
  const confidenceDelta = runB.confidence - runA.confidence;
  const durationDelta = runB.duration_ms - runA.duration_ms;
  
  // Determine performance change
  let performanceChange: RunDelta["performance_change"];
  if (confidenceDelta > 0.05 && durationDelta <= 0) {
    performanceChange = "improved";
  } else if (confidenceDelta < -0.05 || durationDelta > runA.duration_ms * 0.2) {
    performanceChange = "degraded";
  } else {
    performanceChange = "stable";
  }
  
  // Compute metric deltas
  const metricDeltas: Record<string, number> = {};
  const allMetricKeys = new Set([
    ...Object.keys(runA.metrics || {}),
    ...Object.keys(runB.metrics || {})
  ]);
  
  for (const key of allMetricKeys) {
    const valA = (runA.metrics as any)?.[key] || 0;
    const valB = (runB.metrics as any)?.[key] || 0;
    metricDeltas[key] = valB - valA;
  }
  
  const delta: RunDelta = {
    run_a: idA,
    run_b: idB,
    timestamp: new Date().toISOString(),
    confidence_delta: parseFloat(confidenceDelta.toFixed(4)),
    duration_delta_ms: durationDelta,
    performance_change: performanceChange,
    metric_deltas: metricDeltas
  };
  
  // Save delta report
  const deltaPath = path.join(HISTORY_DIR, `delta-${idA}-${idB}.json`);
  fs.writeFileSync(deltaPath, JSON.stringify(delta, null, 2));
  
  console.log(`📈 Evolution: Compared ${idA} → ${idB}: ${performanceChange}`);
  return delta;
}

// Get latest run of a specific type
export function getLatestRun(type?: RunRecord["type"]): RunRecord | null {
  const runs = getAllRuns();
  const filtered = type ? runs.filter(r => r.type === type) : runs;
  
  if (filtered.length === 0) return null;
  
  return filtered.sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )[0];
}

// Get run statistics
export function getRunStats(): {
  total_runs: number;
  by_type: Record<string, number>;
  avg_confidence: number;
  avg_duration_ms: number;
  success_rate: number;
} {
  const runs = getAllRuns();
  
  if (runs.length === 0) {
    return {
      total_runs: 0,
      by_type: {},
      avg_confidence: 0,
      avg_duration_ms: 0,
      success_rate: 0
    };
  }
  
  const byType: Record<string, number> = {};
  let totalConfidence = 0;
  let totalDuration = 0;
  let successCount = 0;
  
  for (const run of runs) {
    byType[run.type] = (byType[run.type] || 0) + 1;
    totalConfidence += run.confidence;
    totalDuration += run.duration_ms;
    if (run.status === "success") successCount++;
  }
  
  return {
    total_runs: runs.length,
    by_type: byType,
    avg_confidence: parseFloat((totalConfidence / runs.length).toFixed(4)),
    avg_duration_ms: Math.round(totalDuration / runs.length),
    success_rate: parseFloat((successCount / runs.length).toFixed(4))
  };
}

// Clean up old runs (keep last N)
export function pruneHistory(keepCount: number = 100): number {
  const runs = getAllRuns();
  
  if (runs.length <= keepCount) {
    return 0;
  }
  
  // Sort by timestamp descending
  runs.sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
  
  const toKeep = runs.slice(0, keepCount);
  const toRemove = runs.slice(keepCount);
  
  // Delete old run files
  for (const run of toRemove) {
    const runPath = path.join(HISTORY_DIR, `${run.id}.json`);
    if (fs.existsSync(runPath)) {
      fs.unlinkSync(runPath);
    }
  }
  
  // Update index
  saveRunIndex(toKeep);
  
  console.log(`🧹 Evolution: Pruned ${toRemove.length} old runs`);
  return toRemove.length;
}

// Export for testing
export { HISTORY_DIR, ensureHistoryDir };
