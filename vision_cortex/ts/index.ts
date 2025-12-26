/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vc.ceo
 * Validator: pending
 * 
 * Vision Cortex — 9-Agent Cognitive Pipeline
 */

import {
  runCrawler,
  runIngestor,
  runOrganizer,
  runPredictor,
  runVisionary,
  runStrategist,
  runValidator,
  runCEO,
  runDocumentor
} from "./agents";
import { validateResult } from "./validator/validatorClient";

export interface CortexPayload {
  mode: "DRY_RUN" | "LIVE";
  signal?: string;
  sources?: string[];
  timestamp?: string;
}

export interface CortexContext {
  start: number;
  payload: CortexPayload;
  signals?: any;
  normalized?: any;
  memory?: any;
  predictions?: any;
  insights?: any;
  decisions?: any;
  audit?: any;
  exec?: any;
  narrative?: string;
  [key: string]: any;
}

export async function runVisionCortex(payload: CortexPayload): Promise<any> {
  console.log("🧠 Vision Cortex booting:", payload.mode);
  console.log("═".repeat(60));
  
  const ctx: CortexContext = { 
    start: Date.now(), 
    payload,
    timestamp: new Date().toISOString()
  };

  try {
    // Execute 9-agent cognitive pipeline
    ctx.crawler    = await runCrawler(ctx);
    ctx.ingestor   = await runIngestor(ctx);
    ctx.organizer  = await runOrganizer(ctx);
    ctx.predictor  = await runPredictor(ctx);
    ctx.visionary  = await runVisionary(ctx);
    ctx.strategist = await runStrategist(ctx);
    ctx.validator  = await runValidator(ctx);
    ctx.ceo        = await runCEO(ctx);
    ctx.documentor = await runDocumentor(ctx);

    // Validate with MCP
    const verdict = await validateResult(ctx.validator);
    
    console.log("═".repeat(60));
    console.log("✅ Validator verdict:", JSON.stringify(verdict, null, 2));
    console.log(`⏱️  Total time: ${Date.now() - ctx.start}ms`);
    
    return verdict;
  } catch (error) {
    console.error("❌ Vision Cortex failed:", error);
    return { status: "failed", error: String(error) };
  }
}

// CLI entry point
const args = process.argv.slice(2);
const mode = args.find(a => a.startsWith("--mode="))?.split("=")[1] || "DRY_RUN";

runVisionCortex({ 
  mode: mode as CortexPayload["mode"],
  timestamp: new Date().toISOString(),
  sources: ["internal", "external", "archive"]
});
