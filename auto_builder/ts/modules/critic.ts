/**
 * MCP-Controlled File
 * Contract: contracts/builder_agent_contracts.json
 * Agent: builder.critic
 * Validator: pending
 */

export interface CriticReport {
  issues: string[];
  warnings: string[];
  score: "PASS" | "WARN" | "FAIL";
  confidence: number;
  timestamp: string;
}

export async function runCritic(ctx: any): Promise<CriticReport> {
  console.log("🔍 Critic: auditing generated files");
  
  const issues: string[] = [];
  const warnings: string[] = [];

  // Validate file types
  for (const f of ctx.synthOutput.filesGenerated) {
    if (!f.endsWith(".ts") && !f.endsWith(".json")) {
      issues.push(`Non-standard file type: ${f}`);
    }
  }

  // Check contract references
  if (!ctx.plan.contracts || ctx.plan.contracts.length === 0) {
    warnings.push("No contracts referenced in build plan");
  }

  // Check governance level
  if (ctx.payload.mode === "LIVE" && ctx.plan.governance_level !== "CRITICAL") {
    warnings.push("LIVE mode should use CRITICAL governance level");
  }

  const score = issues.length > 0 ? "FAIL" : warnings.length > 0 ? "WARN" : "PASS";
  const confidence = score === "PASS" ? 1.0 : score === "WARN" ? 0.7 : 0.3;

  const report: CriticReport = {
    issues,
    warnings,
    score,
    confidence,
    timestamp: new Date().toISOString()
  };

  console.log(`   → Score: ${score} (${issues.length} issues, ${warnings.length} warnings)`);
  ctx.critic = report;
  return report;
}
