/**
 * MCP-Controlled File
 * Contract: contracts/builder_agent_contracts.json
 * Agent: builder.guardian
 * Validator: pending
 */

export interface GuardianReport {
  buildId: string;
  validation: "APPROVED" | "REVIEW" | "REJECTED";
  governance: {
    level: string;
    dry_run_enforced: boolean;
    audit_complete: boolean;
  };
  signature: string;
  timestamp: string;
}

export async function runGuardian(ctx: any): Promise<GuardianReport> {
  console.log("🛡️  Guardian: final compliance check");
  
  // Determine validation status based on critic score
  let validation: GuardianReport["validation"];
  if (ctx.critic.score === "PASS") {
    validation = "APPROVED";
  } else if (ctx.critic.score === "WARN") {
    validation = "REVIEW";
  } else {
    validation = "REJECTED";
  }

  // Enforce DRY_RUN for non-APPROVED builds
  const dryRunEnforced = ctx.payload.mode === "DRY_RUN" || validation !== "APPROVED";

  const report: GuardianReport = {
    buildId: ctx.plan.id,
    validation,
    governance: {
      level: ctx.plan.governance_level,
      dry_run_enforced: dryRunEnforced,
      audit_complete: true
    },
    signature: `guardian-${Date.now()}-pending`,
    timestamp: new Date().toISOString()
  };

  console.log(`   → Validation: ${validation}`);
  console.log(`   → DRY_RUN enforced: ${dryRunEnforced}`);

  ctx.guardianReport = report;
  return report;
}
