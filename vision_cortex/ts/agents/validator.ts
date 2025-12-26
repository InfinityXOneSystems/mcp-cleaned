/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vc.validator
 * Validator: self
 * 
 * Compliance Auditor — Evaluates strategist outputs for accuracy and governance fit
 */

export interface ValidationIssue {
  decision_id: string;
  type: "WARNING" | "ERROR";
  message: string;
}

export interface ValidatorOutput {
  total: number;
  passed: number;
  flagged: number;
  issues: ValidationIssue[];
  result: "PASS" | "REVIEW" | "FAIL";
  confidence: number;
  timestamp: string;
}

export async function runValidator(ctx: any): Promise<ValidatorOutput> {
  console.log("🔍 Validator: auditing strategy consistency");
  
  const issues: ValidationIssue[] = [];
  
  // Validate each decision
  for (const decision of ctx.decisions) {
    // Check confidence threshold
    if (decision.confidence < 0.3) {
      issues.push({
        decision_id: decision.id,
        type: "WARNING",
        message: `Low confidence (${decision.confidence}) on action: ${decision.action}`
      });
    }
    
    // Check high-risk high-priority combinations
    if (decision.priority === "HIGH" && decision.risk > 0.6) {
      issues.push({
        decision_id: decision.id,
        type: "WARNING",
        message: `High priority action has elevated risk (${decision.risk})`
      });
    }
    
    // Check for contradictory actions on same topic
    const relatedDecisions = ctx.decisions.filter(
      (d: any) => d.id !== decision.id && 
        decision.action.includes(d.action.split(" ").pop() || "")
    );
    if (relatedDecisions.length > 0) {
      issues.push({
        decision_id: decision.id,
        type: "ERROR",
        message: "Potential conflict with related decisions"
      });
    }
  }
  
  const passed = ctx.decisions.length - issues.filter((i: any) => i.type === "ERROR").length;
  const errorCount = issues.filter((i: any) => i.type === "ERROR").length;
  const warningCount = issues.filter((i: any) => i.type === "WARNING").length;
  
  let result: ValidatorOutput["result"];
  if (errorCount > 0) {
    result = "FAIL";
  } else if (warningCount > 0) {
    result = "REVIEW";
  } else {
    result = "PASS";
  }

  const output: ValidatorOutput = {
    total: ctx.decisions.length,
    passed,
    flagged: issues.length,
    issues,
    result,
    confidence: passed / ctx.decisions.length,
    timestamp: new Date().toISOString()
  };

  console.log(`   → Audit: ${result} (${passed}/${ctx.decisions.length} passed, ${issues.length} issues)`);
  ctx.audit = output;
  return output;
}
