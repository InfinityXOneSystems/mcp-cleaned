/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: dev.evolution
 * Validator: pending
 */

export {
  recordRun,
  getRun,
  getAllRuns,
  compareRuns,
  getLatestRun,
  getRunStats,
  pruneHistory,
  type RunRecord,
  type RunDelta
} from "./evolutionTracker";
