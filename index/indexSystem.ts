/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: idx.system
 * Validator: pending
 * 
 * Index System for Vision Cortex and Auto Builder
 * Tasks:
 *   • Maintain index of agents, prompts, signals, debates, predictions.
 *   • Keys: time, confidence, source, domain.
 *   • Provide searchIndex(criteria) returning filtered results.
 *   • Persist to ./mcp/index/data/index.json.
 */

import fs from "fs";
import path from "path";

const DATA_DIR = path.resolve(__dirname, "data");
const INDEX_PATH = path.join(DATA_DIR, "index.json");

export type IndexType = "agent" | "prompt" | "signal" | "debate" | "prediction" | "decision" | "evolution";

export interface IndexEntry {
  id: string;
  type: IndexType;
  name: string;
  domain: string;
  source: string;
  confidence: number;
  timestamp: string;
  tags: string[];
  metadata: Record<string, any>;
}

export interface IndexSearchCriteria {
  type?: IndexType | IndexType[];
  domain?: string | string[];
  source?: string;
  minConfidence?: number;
  maxConfidence?: number;
  startTime?: string;
  endTime?: string;
  tags?: string[];
  nameContains?: string;
  limit?: number;
  sortBy?: "time" | "confidence" | "name";
  sortOrder?: "asc" | "desc";
}

export interface IndexStats {
  total_entries: number;
  by_type: Record<string, number>;
  by_domain: Record<string, number>;
  avg_confidence: number;
  last_updated: string;
}

// Ensure data directory exists
function ensureDataDir(): void {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
}

// Load index from disk
function loadIndex(): IndexEntry[] {
  ensureDataDir();
  
  if (!fs.existsSync(INDEX_PATH)) {
    return [];
  }
  
  try {
    const content = fs.readFileSync(INDEX_PATH, "utf-8");
    return JSON.parse(content);
  } catch {
    return [];
  }
}

// Save index to disk
function saveIndex(entries: IndexEntry[]): void {
  ensureDataDir();
  fs.writeFileSync(INDEX_PATH, JSON.stringify(entries, null, 2));
}

// Generate unique entry ID
function generateEntryId(type: IndexType): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `${type}-${timestamp}-${random}`;
}

// Add entry to index
export function addEntry(entry: Omit<IndexEntry, "id" | "timestamp">): IndexEntry {
  const entries = loadIndex();
  
  const newEntry: IndexEntry = {
    ...entry,
    id: generateEntryId(entry.type),
    timestamp: new Date().toISOString()
  };
  
  entries.push(newEntry);
  saveIndex(entries);
  
  console.log(`📇 Index: Added ${entry.type} entry "${entry.name}"`);
  return newEntry;
}

// Add multiple entries at once
export function addEntries(items: Omit<IndexEntry, "id" | "timestamp">[]): IndexEntry[] {
  const entries = loadIndex();
  const newEntries: IndexEntry[] = [];
  
  for (const item of items) {
    const newEntry: IndexEntry = {
      ...item,
      id: generateEntryId(item.type),
      timestamp: new Date().toISOString()
    };
    entries.push(newEntry);
    newEntries.push(newEntry);
  }
  
  saveIndex(entries);
  console.log(`📇 Index: Added ${items.length} entries`);
  return newEntries;
}

// Search index with criteria
export function searchIndex(criteria: IndexSearchCriteria): IndexEntry[] {
  let entries = loadIndex();
  
  // Filter by type
  if (criteria.type) {
    const types = Array.isArray(criteria.type) ? criteria.type : [criteria.type];
    entries = entries.filter(e => types.includes(e.type));
  }
  
  // Filter by domain
  if (criteria.domain) {
    const domains = Array.isArray(criteria.domain) ? criteria.domain : [criteria.domain];
    entries = entries.filter(e => domains.includes(e.domain));
  }
  
  // Filter by source
  if (criteria.source) {
    entries = entries.filter(e => e.source === criteria.source);
  }
  
  // Filter by confidence range
  if (criteria.minConfidence !== undefined) {
    entries = entries.filter(e => e.confidence >= criteria.minConfidence!);
  }
  if (criteria.maxConfidence !== undefined) {
    entries = entries.filter(e => e.confidence <= criteria.maxConfidence!);
  }
  
  // Filter by time range
  if (criteria.startTime) {
    const startDate = new Date(criteria.startTime);
    entries = entries.filter(e => new Date(e.timestamp) >= startDate);
  }
  if (criteria.endTime) {
    const endDate = new Date(criteria.endTime);
    entries = entries.filter(e => new Date(e.timestamp) <= endDate);
  }
  
  // Filter by tags
  if (criteria.tags && criteria.tags.length > 0) {
    entries = entries.filter(e => 
      criteria.tags!.some(tag => e.tags.includes(tag))
    );
  }
  
  // Filter by name
  if (criteria.nameContains) {
    const search = criteria.nameContains.toLowerCase();
    entries = entries.filter(e => e.name.toLowerCase().includes(search));
  }
  
  // Sort
  const sortBy = criteria.sortBy || "time";
  const sortOrder = criteria.sortOrder || "desc";
  
  entries.sort((a, b) => {
    let comparison = 0;
    
    switch (sortBy) {
      case "time":
        comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
        break;
      case "confidence":
        comparison = a.confidence - b.confidence;
        break;
      case "name":
        comparison = a.name.localeCompare(b.name);
        break;
    }
    
    return sortOrder === "asc" ? comparison : -comparison;
  });
  
  // Limit results
  if (criteria.limit && criteria.limit > 0) {
    entries = entries.slice(0, criteria.limit);
  }
  
  return entries;
}

// Get entry by ID
export function getEntry(id: string): IndexEntry | null {
  const entries = loadIndex();
  return entries.find(e => e.id === id) || null;
}

// Update entry
export function updateEntry(id: string, updates: Partial<Omit<IndexEntry, "id">>): IndexEntry | null {
  const entries = loadIndex();
  const index = entries.findIndex(e => e.id === id);
  
  if (index === -1) {
    return null;
  }
  
  entries[index] = { ...entries[index], ...updates };
  saveIndex(entries);
  
  console.log(`📇 Index: Updated entry ${id}`);
  return entries[index];
}

// Delete entry
export function deleteEntry(id: string): boolean {
  const entries = loadIndex();
  const initialLength = entries.length;
  const filtered = entries.filter(e => e.id !== id);
  
  if (filtered.length === initialLength) {
    return false;
  }
  
  saveIndex(filtered);
  console.log(`📇 Index: Deleted entry ${id}`);
  return true;
}

// Get index statistics
export function getIndexStats(): IndexStats {
  const entries = loadIndex();
  
  if (entries.length === 0) {
    return {
      total_entries: 0,
      by_type: {},
      by_domain: {},
      avg_confidence: 0,
      last_updated: new Date().toISOString()
    };
  }
  
  const byType: Record<string, number> = {};
  const byDomain: Record<string, number> = {};
  let totalConfidence = 0;
  
  for (const entry of entries) {
    byType[entry.type] = (byType[entry.type] || 0) + 1;
    byDomain[entry.domain] = (byDomain[entry.domain] || 0) + 1;
    totalConfidence += entry.confidence;
  }
  
  // Find most recent entry
  const sorted = [...entries].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
  
  return {
    total_entries: entries.length,
    by_type: byType,
    by_domain: byDomain,
    avg_confidence: parseFloat((totalConfidence / entries.length).toFixed(4)),
    last_updated: sorted[0].timestamp
  };
}

// Index agents from contracts
export function indexAgentsFromContracts(contractsPath: string): IndexEntry[] {
  if (!fs.existsSync(contractsPath)) {
    console.error(`❌ Contract file not found: ${contractsPath}`);
    return [];
  }
  
  const content = fs.readFileSync(contractsPath, "utf-8");
  const contracts = JSON.parse(content);
  
  const agentEntries: Omit<IndexEntry, "id" | "timestamp">[] = [];
  
  for (const agent of contracts.agents || []) {
    agentEntries.push({
      type: "agent",
      name: agent.id || agent.name,
      domain: agent.domain || "system",
      source: contractsPath,
      confidence: 1.0,
      tags: agent.tags || [agent.role],
      metadata: {
        role: agent.role,
        input: agent.input,
        output: agent.output,
        governance: agent.governance
      }
    });
  }
  
  return addEntries(agentEntries);
}

// Clear all entries
export function clearIndex(): void {
  saveIndex([]);
  console.log("📇 Index: Cleared all entries");
}

// Export for external use
export { DATA_DIR, INDEX_PATH };
