/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: memory.gateway
 * Validator: pending
 */

export {
  saveContext,
  queryMemory,
  getHistory,
  vectorSearch,
  cleanupExpired,
  getMemoryStats,
  clearAgentMemory,
  type MemoryEntry,
  type MemoryQuery,
  type VectorSearchResult
} from "./memoryGateway";
