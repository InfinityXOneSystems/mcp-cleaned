/**
 * MCP-Controlled File
 * Contract: contracts/builder_agent_contracts.json
 * Agent: builder.architect
 * Validator: pending
 * 
 * Auto Builder — 5-Agent Execution Chain
 */

import { runArchitect } from "./modules/architect";
import { runSynthesizer } from "./modules/synthesizer";
import { runCritic } from "./modules/critic";
import { runIntegrator } from "./modules/integrator";
import { runGuardian } from "./modules/guardian";
import { validateResult } from "./validator/validatorClient";

export interface BuildPayload {
  mode: "DRY_RUN" | "VALIDATED" | "LIVE";
  planPath?: string;
  timestamp?: string;
}

export interface BuildContext {
  start: number;
  payload: BuildPayload;
  plan?: any;
  synthOutput?: any;
  critic?: any;
  integration?: any;
  guardianReport?: any;
  [key: string]: any;
}

export async function runAutoBuilder(payload: BuildPayload): Promise<any> {
  console.log("🚀 Auto Builder starting:", payload.mode);
  console.log("─".repeat(50));

  const ctx: BuildContext = { 
    start: Date.now(), 
    payload,
    timestamp: new Date().toISOString()
  };

  try {
    // Execute 5-agent pipeline
    ctx.architect = await runArchitect(ctx);
    ctx.synthesizer = await runSynthesizer(ctx);
    ctx.critic = await runCritic(ctx);
    ctx.integrator = await runIntegrator(ctx);
    ctx.guardian = await runGuardian(ctx);

    // Validate with MCP
    const verdict = await validateResult(ctx.guardian);
    
    console.log("─".repeat(50));
    console.log("✅ Validator verdict:", JSON.stringify(verdict, null, 2));
    console.log(`⏱️  Total time: ${Date.now() - ctx.start}ms`);
    
    return verdict;
  } catch (error) {
    console.error("❌ Auto Builder failed:", error);
    return { status: "failed", error: String(error) };
  }
}

// CLI entry point
const args = process.argv.slice(2);
const mode = args.find(a => a.startsWith("--mode="))?.split("=")[1] || "DRY_RUN";

runAutoBuilder({ 
  mode: mode as BuildPayload["mode"],
  timestamp: new Date().toISOString()
});
