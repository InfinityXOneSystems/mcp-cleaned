/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vc.documentor
 * Validator: pending
 * 
 * Narrative Generator — Translates validated decisions into human-readable reports
 */

import fs from "fs";
import path from "path";

export interface DocumentorOutput {
  narrative: string;
  format: string;
  length: number;
  file_path: string;
  timestamp: string;
}

export async function runDocumentor(ctx: any): Promise<DocumentorOutput> {
  console.log("📝 Documentor: writing narrative output");
  
  const now = new Date();
  const dateStr = now.toISOString().split("T")[0];
  
  // Build narrative report
  const lines: string[] = [
    "═".repeat(60),
    "VISION CORTEX INTELLIGENCE REPORT",
    `Generated: ${now.toISOString()}`,
    "═".repeat(60),
    "",
    "EXECUTIVE SUMMARY",
    "-".repeat(40),
    `Status: ${ctx.audit.result}`,
    `Confidence Delta: ${ctx.exec.confidence_delta > 0 ? "+" : ""}${(ctx.exec.confidence_delta * 100).toFixed(1)}%`,
    `Actions Approved: ${ctx.exec.approved_actions.length}/${ctx.exec.total_decisions}`,
    "",
    "INSIGHTS",
    "-".repeat(40),
  ];
  
  // Add insights
  for (const insight of ctx.insights || []) {
    lines.push(`• [${insight.pattern}] ${insight.narrative}`);
    lines.push(`  Significance: ${(insight.significance * 100).toFixed(0)}%`);
    lines.push("");
  }
  
  lines.push("APPROVED ACTIONS");
  lines.push("-".repeat(40));
  
  // Add approved actions by priority
  const highPriority = ctx.exec.approved_actions.filter((a: any) => a.priority === "HIGH");
  const medPriority = ctx.exec.approved_actions.filter((a: any) => a.priority === "MEDIUM");
  const lowPriority = ctx.exec.approved_actions.filter((a: any) => a.priority === "LOW");
  
  if (highPriority.length > 0) {
    lines.push("");
    lines.push("🔴 HIGH PRIORITY:");
    for (const action of highPriority) {
      lines.push(`  → ${action.action}`);
    }
  }
  
  if (medPriority.length > 0) {
    lines.push("");
    lines.push("🟡 MEDIUM PRIORITY:");
    for (const action of medPriority) {
      lines.push(`  → ${action.action}`);
    }
  }
  
  if (lowPriority.length > 0) {
    lines.push("");
    lines.push("🟢 LOW PRIORITY:");
    for (const action of lowPriority) {
      lines.push(`  → ${action.action}`);
    }
  }
  
  // Validation issues
  if (ctx.audit.issues.length > 0) {
    lines.push("");
    lines.push("VALIDATION NOTES");
    lines.push("-".repeat(40));
    for (const issue of ctx.audit.issues) {
      const icon = issue.type === "ERROR" ? "❌" : "⚠️";
      lines.push(`${icon} ${issue.message}`);
    }
  }
  
  lines.push("");
  lines.push("═".repeat(60));
  lines.push(`Next Review: ${ctx.exec.next_review}`);
  lines.push(`Signature: ${ctx.exec.signature}`);
  lines.push("═".repeat(60));
  
  const narrative = lines.join("\n");
  
  // Write to file
  const filePath = path.resolve(`./vision_cortex_report_${dateStr}.txt`);
  fs.writeFileSync(filePath, narrative);
  
  // Also write JSON version
  const jsonPath = path.resolve(`./vision_cortex_report_${dateStr}.json`);
  fs.writeFileSync(jsonPath, JSON.stringify({
    executive_summary: ctx.exec,
    insights: ctx.insights,
    decisions: ctx.decisions,
    validation: ctx.audit,
    timestamp: now.toISOString()
  }, null, 2));

  const output: DocumentorOutput = {
    narrative,
    format: "txt",
    length: narrative.length,
    file_path: filePath,
    timestamp: now.toISOString()
  };

  console.log(`   → Report saved: ${filePath}`);
  ctx.narrative = narrative;
  return output;
}
