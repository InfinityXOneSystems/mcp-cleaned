/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vc.strategist
 * Validator: pending
 * 
 * Decision Architect — Converts insights into prioritized actions
 */

export interface Decision {
  id: string;
  action: string;
  rationale: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  impact: number;
  risk: number;
  confidence: number;
  based_on: string[];
  timestamp: string;
}

export interface StrategistOutput {
  decisions: Decision[];
  total_actions: number;
  high_priority: number;
  timestamp: string;
}

export async function runStrategist(ctx: any): Promise<StrategistOutput> {
  console.log("🧭 Strategist: forming action recommendations");
  
  const decisions: Decision[] = [];
  
  // Generate decisions from predictions
  for (const pred of ctx.predictions) {
    const impact = pred.magnitude;
    const risk = pred.trend === "down" ? 0.7 : 0.3;
    const confidence = pred.confidence;
    
    // Calculate priority score
    const priorityScore = (impact * 0.4) + (confidence * 0.4) + ((1 - risk) * 0.2);
    const priority = priorityScore > 0.7 ? "HIGH" : priorityScore > 0.4 ? "MEDIUM" : "LOW";
    
    let action: string;
    if (pred.trend === "up") {
      action = `Increase investment/focus in ${pred.topic}`;
    } else if (pred.trend === "down") {
      action = `Reduce exposure to ${pred.topic}, seek alternatives`;
    } else {
      action = `Monitor ${pred.topic} for emerging signals`;
    }
    
    decisions.push({
      id: `decision-${Date.now()}-${pred.topic}`,
      action,
      rationale: pred.reasoning,
      priority,
      impact: parseFloat(impact.toFixed(3)),
      risk: parseFloat(risk.toFixed(3)),
      confidence: parseFloat(confidence.toFixed(3)),
      based_on: [pred.id],
      timestamp: new Date().toISOString()
    });
  }

  // Sort by priority
  decisions.sort((a, b) => {
    const priorityOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  const output: StrategistOutput = {
    decisions,
    total_actions: decisions.length,
    high_priority: decisions.filter(d => d.priority === "HIGH").length,
    timestamp: new Date().toISOString()
  };

  console.log(`   → Generated ${decisions.length} decisions (${output.high_priority} high priority)`);
  ctx.decisions = decisions;
  return output;
}
