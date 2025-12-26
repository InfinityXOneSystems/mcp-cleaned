/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: memory.gateway
 * Validator: pending
 * 
 * Unified Memory Model
 * Persistence: Firestore + vector DB.
 * Functions: saveContext(agent, data), queryMemory(query), getHistory(agent).
 * Respect environment vars MCP_FIRESTORE_PROJECT and MCP_VECTOR_ENDPOINT.
 */

import fs from "fs";
import path from "path";

// Environment configuration
const FIRESTORE_PROJECT = process.env.MCP_FIRESTORE_PROJECT || process.env.FIRESTORE_PROJECT || "infinity-x-one-systems";
const FIRESTORE_COLLECTION = process.env.MCP_FIRESTORE_COLLECTION || process.env.FIRESTORE_COLLECTION || "mcp_memory";
const VECTOR_ENDPOINT = process.env.MCP_VECTOR_ENDPOINT || "http://localhost:8001/vectors";

// Local fallback storage
const LOCAL_MEMORY_DIR = path.resolve(__dirname, "data");
const LOCAL_MEMORY_PATH = path.join(LOCAL_MEMORY_DIR, "memory.json");

export interface MemoryEntry {
  id: string;
  agent: string;
  type: "context" | "prediction" | "decision" | "signal" | "evolution";
  data: Record<string, any>;
  embedding?: number[];
  timestamp: string;
  ttl?: number;  // Time-to-live in seconds
  tags: string[];
  confidence?: number;
}

export interface MemoryQuery {
  agent?: string;
  type?: MemoryEntry["type"] | MemoryEntry["type"][];
  tags?: string[];
  minConfidence?: number;
  startTime?: string;
  endTime?: string;
  limit?: number;
  semantic?: string;  // For vector search
}

export interface VectorSearchResult {
  id: string;
  score: number;
  entry: MemoryEntry;
}

// Firestore client (lazy initialized)
let firestoreClient: any = null;

async function getFirestoreClient(): Promise<any | null> {
  if (firestoreClient) return firestoreClient;
  
  try {
    // Dynamic import to avoid hard dependency
    const { Firestore } = await import("@google-cloud/firestore");
    firestoreClient = new Firestore({
      projectId: FIRESTORE_PROJECT
    });
    console.log(`🔥 Firestore: Connected to ${FIRESTORE_PROJECT}`);
    return firestoreClient;
  } catch (error) {
    console.warn("⚠️  Firestore unavailable, using local storage");
    return null;
  }
}

// Ensure local storage directory exists
function ensureLocalStorage(): void {
  if (!fs.existsSync(LOCAL_MEMORY_DIR)) {
    fs.mkdirSync(LOCAL_MEMORY_DIR, { recursive: true });
  }
}

// Load local memory
function loadLocalMemory(): MemoryEntry[] {
  ensureLocalStorage();
  
  if (!fs.existsSync(LOCAL_MEMORY_PATH)) {
    return [];
  }
  
  try {
    const content = fs.readFileSync(LOCAL_MEMORY_PATH, "utf-8");
    return JSON.parse(content);
  } catch {
    return [];
  }
}

// Save local memory
function saveLocalMemory(entries: MemoryEntry[]): void {
  ensureLocalStorage();
  fs.writeFileSync(LOCAL_MEMORY_PATH, JSON.stringify(entries, null, 2));
}

// Generate unique ID
function generateId(): string {
  return `mem-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Save context/data for an agent
 */
export async function saveContext(
  agent: string,
  data: Record<string, any>,
  options?: {
    type?: MemoryEntry["type"];
    tags?: string[];
    confidence?: number;
    ttl?: number;
  }
): Promise<MemoryEntry> {
  const entry: MemoryEntry = {
    id: generateId(),
    agent,
    type: options?.type || "context",
    data,
    timestamp: new Date().toISOString(),
    tags: options?.tags || [],
    confidence: options?.confidence,
    ttl: options?.ttl
  };
  
  // Try Firestore first
  const firestore = await getFirestoreClient();
  
  if (firestore) {
    try {
      await firestore
        .collection(FIRESTORE_COLLECTION)
        .doc(entry.id)
        .set(entry);
      console.log(`💾 Memory: Saved to Firestore [${entry.id}]`);
    } catch (error) {
      console.error("❌ Firestore save failed:", error);
      // Fall through to local storage
    }
  }
  
  // Always save to local storage as backup
  const localEntries = loadLocalMemory();
  localEntries.push(entry);
  saveLocalMemory(localEntries);
  
  return entry;
}

/**
 * Query memory with filters
 */
export async function queryMemory(query: MemoryQuery): Promise<MemoryEntry[]> {
  let entries: MemoryEntry[] = [];
  
  // Try Firestore first
  const firestore = await getFirestoreClient();
  
  if (firestore) {
    try {
      let firestoreQuery = firestore.collection(FIRESTORE_COLLECTION);
      
      // Apply filters
      if (query.agent) {
        firestoreQuery = firestoreQuery.where("agent", "==", query.agent);
      }
      
      if (query.type) {
        const types = Array.isArray(query.type) ? query.type : [query.type];
        if (types.length === 1) {
          firestoreQuery = firestoreQuery.where("type", "==", types[0]);
        }
      }
      
      if (query.minConfidence !== undefined) {
        firestoreQuery = firestoreQuery.where("confidence", ">=", query.minConfidence);
      }
      
      // Execute query
      const snapshot = await firestoreQuery
        .orderBy("timestamp", "desc")
        .limit(query.limit || 100)
        .get();
      
      entries = snapshot.docs.map((doc: any) => doc.data() as MemoryEntry);
    } catch (error) {
      console.warn("⚠️  Firestore query failed, using local:", error);
    }
  }
  
  // Fall back to or supplement with local storage
  if (entries.length === 0) {
    entries = loadLocalMemory();
    
    // Apply filters locally
    if (query.agent) {
      entries = entries.filter(e => e.agent === query.agent);
    }
    
    if (query.type) {
      const types = Array.isArray(query.type) ? query.type : [query.type];
      entries = entries.filter(e => types.includes(e.type));
    }
    
    if (query.tags && query.tags.length > 0) {
      entries = entries.filter(e => 
        query.tags!.some(tag => e.tags.includes(tag))
      );
    }
    
    if (query.minConfidence !== undefined) {
      entries = entries.filter(e => 
        e.confidence !== undefined && e.confidence >= query.minConfidence!
      );
    }
    
    if (query.startTime) {
      const startDate = new Date(query.startTime);
      entries = entries.filter(e => new Date(e.timestamp) >= startDate);
    }
    
    if (query.endTime) {
      const endDate = new Date(query.endTime);
      entries = entries.filter(e => new Date(e.timestamp) <= endDate);
    }
    
    // Sort by timestamp descending
    entries.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    
    // Apply limit
    if (query.limit && query.limit > 0) {
      entries = entries.slice(0, query.limit);
    }
  }
  
  // If semantic query provided, try vector search
  if (query.semantic) {
    const vectorResults = await vectorSearch(query.semantic, entries);
    if (vectorResults.length > 0) {
      entries = vectorResults.map(r => r.entry);
    }
  }
  
  return entries;
}

/**
 * Get history for a specific agent
 */
export async function getHistory(
  agent: string,
  limit: number = 50
): Promise<MemoryEntry[]> {
  return queryMemory({ agent, limit });
}

/**
 * Vector search (semantic similarity)
 */
export async function vectorSearch(
  query: string,
  entries?: MemoryEntry[],
  limit: number = 10
): Promise<VectorSearchResult[]> {
  try {
    const response = await fetch(`${VECTOR_ENDPOINT}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, limit })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const results = await response.json();
    return results as VectorSearchResult[];
  } catch (error) {
    console.warn("⚠️  Vector search unavailable:", error);
    
    // Fallback: simple keyword matching
    if (entries) {
      const queryLower = query.toLowerCase();
      const scored = entries
        .map(entry => {
          const content = JSON.stringify(entry.data).toLowerCase();
          const matches = queryLower.split(" ").filter(word => 
            content.includes(word)
          );
          return {
            id: entry.id,
            score: matches.length / queryLower.split(" ").length,
            entry
          };
        })
        .filter(r => r.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, limit);
      
      return scored;
    }
    
    return [];
  }
}

/**
 * Delete expired entries (based on TTL)
 */
export async function cleanupExpired(): Promise<number> {
  const now = Date.now();
  let cleaned = 0;
  
  // Clean local storage
  const localEntries = loadLocalMemory();
  const validEntries = localEntries.filter(entry => {
    if (!entry.ttl) return true;  // No TTL = keep forever
    
    const expiresAt = new Date(entry.timestamp).getTime() + (entry.ttl * 1000);
    if (now > expiresAt) {
      cleaned++;
      return false;
    }
    return true;
  });
  
  saveLocalMemory(validEntries);
  
  // Clean Firestore (if available)
  const firestore = await getFirestoreClient();
  if (firestore) {
    try {
      const snapshot = await firestore
        .collection(FIRESTORE_COLLECTION)
        .where("ttl", ">", 0)
        .get();
      
      const batch = firestore.batch();
      let batchCount = 0;
      
      snapshot.docs.forEach((doc: any) => {
        const entry = doc.data() as MemoryEntry;
        if (entry.ttl) {
          const expiresAt = new Date(entry.timestamp).getTime() + (entry.ttl * 1000);
          if (now > expiresAt) {
            batch.delete(doc.ref);
            batchCount++;
          }
        }
      });
      
      if (batchCount > 0) {
        await batch.commit();
        cleaned += batchCount;
      }
    } catch (error) {
      console.error("❌ Firestore cleanup failed:", error);
    }
  }
  
  if (cleaned > 0) {
    console.log(`🧹 Memory: Cleaned up ${cleaned} expired entries`);
  }
  
  return cleaned;
}

/**
 * Get memory statistics
 */
export async function getMemoryStats(): Promise<{
  total_entries: number;
  by_agent: Record<string, number>;
  by_type: Record<string, number>;
  storage_mode: "firestore" | "local" | "hybrid";
}> {
  const entries = await queryMemory({ limit: 10000 });
  
  const byAgent: Record<string, number> = {};
  const byType: Record<string, number> = {};
  
  for (const entry of entries) {
    byAgent[entry.agent] = (byAgent[entry.agent] || 0) + 1;
    byType[entry.type] = (byType[entry.type] || 0) + 1;
  }
  
  const firestore = await getFirestoreClient();
  
  return {
    total_entries: entries.length,
    by_agent: byAgent,
    by_type: byType,
    storage_mode: firestore ? "hybrid" : "local"
  };
}

/**
 * Delete all memory for an agent
 */
export async function clearAgentMemory(agent: string): Promise<number> {
  let deleted = 0;
  
  // Clear local
  const localEntries = loadLocalMemory();
  const remaining = localEntries.filter(e => {
    if (e.agent === agent) {
      deleted++;
      return false;
    }
    return true;
  });
  saveLocalMemory(remaining);
  
  // Clear Firestore
  const firestore = await getFirestoreClient();
  if (firestore) {
    try {
      const snapshot = await firestore
        .collection(FIRESTORE_COLLECTION)
        .where("agent", "==", agent)
        .get();
      
      const batch = firestore.batch();
      snapshot.docs.forEach((doc: any) => {
        batch.delete(doc.ref);
        deleted++;
      });
      await batch.commit();
    } catch (error) {
      console.error("❌ Firestore clear failed:", error);
    }
  }
  
  console.log(`🗑️  Memory: Cleared ${deleted} entries for agent ${agent}`);
  return deleted;
}

// Export configuration
export { FIRESTORE_PROJECT, FIRESTORE_COLLECTION, VECTOR_ENDPOINT, LOCAL_MEMORY_DIR };
