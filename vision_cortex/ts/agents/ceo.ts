/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vc.ceo
 * Validator: pending
 * 
 * Executive Integrator — Oversees all agent interactions and confidence deltas
 */

export interface ApprovedAction {
  decision_id: string;
  action: string;
  priority: string;
  approved_by: string;
}

export interface ExecutiveReport {
  date: string;
  summary: string;
  total_decisions: number;
  approved_actions: ApprovedAction[];
  deferred_actions: string[];
  confidence_delta: number;
  next_review: string;
  signature: string;
}

export async function runCEO(ctx: any): Promise<ExecutiveReport> {
  console.log("🏛️  CEO: integrating validated strategy");
  
  // Filter approved actions based on validation
  const approvedActions: ApprovedAction[] = ctx.decisions
    .filter((d: any) => {
      const hasError = ctx.audit.issues.some(
        (i: any) => i.decision_id === d.id && i.type === "ERROR"
      );
      return !hasError;
    })
    .map((d: any) => ({
      decision_id: d.id,
      action: d.action,
      priority: d.priority,
      approved_by: "vc.ceo"
    }));

  const deferredActions = ctx.decisions
    .filter((d: any) => {
      const hasError = ctx.audit.issues.some(
        (i: any) => i.decision_id === d.id && i.type === "ERROR"
      );
      return hasError;
    })
    .map((d: any) => d.id);

  // Calculate confidence delta
  const avgConfidence = ctx.decisions.reduce((sum: number, d: any) => sum + d.confidence, 0) / ctx.decisions.length;
  const previousBaseline = 0.6; // Simulated baseline
  const confidenceDelta = avgConfidence - previousBaseline;

  const report: ExecutiveReport = {
    date: new Date().toISOString(),
    summary: ctx.audit.result,
    total_decisions: ctx.decisions.length,
    approved_actions: approvedActions,
    deferred_actions: deferredActions,
    confidence_delta: parseFloat(confidenceDelta.toFixed(3)),
    next_review: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    signature: `ceo-${Date.now()}`
  };

  console.log(`   → Approved ${approvedActions.length}/${ctx.decisions.length} actions`);
  console.log(`   → Confidence delta: ${confidenceDelta > 0 ? "+" : ""}${(confidenceDelta * 100).toFixed(1)}%`);
  
  ctx.exec = report;
  return report;
}
