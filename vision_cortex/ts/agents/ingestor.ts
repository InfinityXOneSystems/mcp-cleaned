/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vc.ingestor
 * Validator: pending
 * 
 * Data Normalizer — Parses crawler outputs into structured documents
 */

export interface NormalizedRecord {
  id: string;
  topic: string;
  normalized_topic: string;
  source: string;
  content: string;
  tags: string[];
  confidence: number;
  ingested_at: string;
}

export interface IngestorOutput {
  records: NormalizedRecord[];
  total_processed: number;
  timestamp: string;
}

export async function runIngestor(ctx: any): Promise<IngestorOutput> {
  console.log("📥 Ingestor: normalizing signals");
  
  const records: NormalizedRecord[] = ctx.signals.map((signal: any) => ({
    id: signal.id.replace("signal", "record"),
    topic: signal.topic,
    normalized_topic: signal.topic.toLowerCase().replace(/\s+/g, "_"),
    source: signal.source,
    content: signal.raw,
    tags: [
      signal.topic.toLowerCase(),
      signal.source,
      "auto-ingested"
    ],
    confidence: signal.confidence,
    ingested_at: new Date().toISOString()
  }));

  const output: IngestorOutput = {
    records,
    total_processed: records.length,
    timestamp: new Date().toISOString()
  };

  console.log(`   → Normalized ${records.length} records`);
  ctx.normalized = records;
  return output;
}
