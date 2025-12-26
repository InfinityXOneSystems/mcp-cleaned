/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vc.organizer
 * Validator: pending
 * 
 * Memory Curator — Clusters ingested data by domain and confidence
 */

export interface MemoryEntry {
  topic: string;
  count: number;
  avg_confidence: number;
  last_seen: string;
  records: string[];
}

export interface OrganizerOutput {
  memory: Record<string, MemoryEntry>;
  clusters: number;
  timestamp: string;
}

export async function runOrganizer(ctx: any): Promise<OrganizerOutput> {
  console.log("🗂️  Organizer: curating memory entries");
  
  // Cluster records by topic
  const memory: Record<string, MemoryEntry> = {};
  
  for (const record of ctx.normalized) {
    const topic = record.normalized_topic;
    
    if (!memory[topic]) {
      memory[topic] = {
        topic,
        count: 0,
        avg_confidence: 0,
        last_seen: record.ingested_at,
        records: []
      };
    }
    
    memory[topic].count++;
    memory[topic].records.push(record.id);
    memory[topic].last_seen = record.ingested_at;
    memory[topic].avg_confidence = 
      (memory[topic].avg_confidence * (memory[topic].count - 1) + record.confidence) / 
      memory[topic].count;
  }

  const output: OrganizerOutput = {
    memory,
    clusters: Object.keys(memory).length,
    timestamp: new Date().toISOString()
  };

  console.log(`   → Organized into ${output.clusters} clusters`);
  ctx.memory = memory;
  return output;
}
