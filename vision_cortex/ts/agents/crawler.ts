/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vc.crawler
 * Validator: pending
 * 
 * Signal Harvester — Crawls approved data sources for intelligence signals
 */

import fs from "fs";
import path from "path";

export interface Signal {
  id: string;
  topic: string;
  source: string;
  timestamp: string;
  raw: string;
  confidence: number;
}

export interface CrawlerOutput {
  signals: Signal[];
  sources_scanned: number;
  timestamp: string;
}

// Strategic seed domains from taxonomy
const DOMAINS = [
  "AI", "Compute", "Economy", "Energy", "Governance",
  "Philosophy", "Technology", "Culture"
];

const SOURCES = [
  "arxiv", "hackernews", "reuters", "internal_memory"
];

export async function runCrawler(ctx: any): Promise<CrawlerOutput> {
  console.log("🌐 Crawler: harvesting external signals");
  
  // Simulate signal harvesting from multiple domains
  const signals: Signal[] = DOMAINS.map((topic, i) => ({
    id: `signal-${Date.now()}-${i}`,
    topic,
    source: SOURCES[i % SOURCES.length],
    timestamp: new Date().toISOString(),
    raw: `Latest developments in ${topic.toLowerCase()} sector`,
    confidence: 0.5 + Math.random() * 0.5
  }));

  const output: CrawlerOutput = {
    signals,
    sources_scanned: SOURCES.length,
    timestamp: new Date().toISOString()
  };

  // Write signals to file
  const signalsPath = path.resolve("./signals.json");
  fs.writeFileSync(signalsPath, JSON.stringify(signals, null, 2));
  console.log(`   → Harvested ${signals.length} signals from ${SOURCES.length} sources`);

  ctx.signals = signals;
  return output;
}
