/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: prompt.manager
 * Validator: pending
 * 
 * Auto Prompt System
 * Functions: loadPrompts(domain), injectPrompt(agent, context).
 * Store prompt templates under mcp/auto_prompts/templates/.
 * Allow Vision Cortex and Auto Builder to request context-aware prompts.
 */

import fs from "fs";
import path from "path";

const TEMPLATES_DIR = path.resolve(__dirname, "templates");

export interface PromptTemplate {
  id: string;
  name: string;
  domain: string;
  level: string;  // L1-L10
  description: string;
  template: string;
  variables: string[];
  tags: string[];
  governance: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface PromptContext {
  agent: string;
  action: string;
  timestamp: string;
  variables: Record<string, any>;
  history?: string[];
}

export interface InjectedPrompt {
  prompt_id: string;
  agent: string;
  content: string;
  injected_at: string;
  variables_used: string[];
}

// Ensure templates directory exists
function ensureTemplatesDir(): void {
  if (!fs.existsSync(TEMPLATES_DIR)) {
    fs.mkdirSync(TEMPLATES_DIR, { recursive: true });
  }
}

// Load all prompts for a domain
export function loadPrompts(domain?: string): PromptTemplate[] {
  ensureTemplatesDir();
  
  const templates: PromptTemplate[] = [];
  
  // Read all JSON files in templates directory
  const files = fs.readdirSync(TEMPLATES_DIR).filter(f => f.endsWith(".json"));
  
  for (const file of files) {
    try {
      const content = fs.readFileSync(path.join(TEMPLATES_DIR, file), "utf-8");
      const template = JSON.parse(content) as PromptTemplate;
      
      if (!domain || template.domain === domain) {
        templates.push(template);
      }
    } catch (error) {
      console.warn(`⚠️  Failed to load template ${file}:`, error);
    }
  }
  
  // Also load built-in prompts if no files exist
  if (templates.length === 0) {
    return getBuiltInPrompts(domain);
  }
  
  return templates;
}

// Get built-in prompts
function getBuiltInPrompts(domain?: string): PromptTemplate[] {
  const builtIn: PromptTemplate[] = [
    {
      id: "L1_MANUAL_ASSIST",
      name: "Manual Assistance",
      domain: "system",
      level: "L1",
      description: "Provide manual assistance with human oversight",
      template: "Agent {{agent}} is assisting with: {{task}}.\nContext: {{context}}\nProvide guidance while awaiting human confirmation.",
      variables: ["agent", "task", "context"],
      tags: ["manual", "human-in-loop"],
      governance: "LOW"
    },
    {
      id: "L3_BACKGROUND_CRAWL",
      name: "Background Crawl",
      domain: "system",
      level: "L3",
      description: "Periodic background data collection",
      template: "Initiate background crawl for {{sources}}.\nDomains: {{domains}}\nMax signals: {{max_signals}}\nStore results in memory registry.",
      variables: ["sources", "domains", "max_signals"],
      tags: ["crawl", "background", "periodic"],
      governance: "LOW"
    },
    {
      id: "L5_AUTOMATED_VALIDATION",
      name: "Automated Validation",
      domain: "system",
      level: "L5",
      description: "Automated validation with confidence thresholds",
      template: "Validate {{artifact}} using {{validation_type}}.\nConfidence threshold: {{threshold}}\nIf confidence >= threshold, proceed automatically.\nOtherwise, flag for human review.",
      variables: ["artifact", "validation_type", "threshold"],
      tags: ["validation", "automated"],
      governance: "MEDIUM"
    },
    {
      id: "L7_AUTONOMOUS_EVOLUTION",
      name: "Autonomous Evolution",
      domain: "evolution",
      level: "L7",
      description: "Self-improvement with governance constraints",
      template: "Analyze performance metrics for {{system}}.\nIdentify optimization opportunities.\nPropose changes within governance level {{governance}}.\nExecute if confidence >= {{threshold}}.",
      variables: ["system", "governance", "threshold"],
      tags: ["evolution", "autonomous", "self-improvement"],
      governance: "HIGH"
    },
    {
      id: "L10_SINGULARITY_GUIDANCE",
      name: "Singularity Guidance",
      domain: "special",
      level: "L10",
      description: "Full autonomous operation with ethical constraints",
      template: "Operating in full autonomous mode.\nEthical constraints: {{constraints}}\nGovernance tier: {{tier}}\nMission: {{mission}}\nAll actions must be logged and auditable.",
      variables: ["constraints", "tier", "mission"],
      tags: ["singularity", "full-auto", "ethical"],
      governance: "CRITICAL"
    },
    {
      id: "VC_CRAWLER_PROMPT",
      name: "Vision Cortex Crawler",
      domain: "vision_cortex",
      level: "L3",
      description: "Signal harvesting prompt for crawler agent",
      template: "Crawl {{sources}} for intelligence signals.\nDomains: {{domains}}\nPrioritize: {{priority_topics}}\nReturn normalized signal objects with confidence scores.",
      variables: ["sources", "domains", "priority_topics"],
      tags: ["crawler", "vision-cortex"],
      governance: "LOW"
    },
    {
      id: "VC_PREDICTOR_PROMPT",
      name: "Vision Cortex Predictor",
      domain: "vision_cortex",
      level: "L5",
      description: "Forecast generation prompt",
      template: "Generate predictions based on memory state.\nTime horizon: {{horizon}}\nConfidence threshold: {{threshold}}\nModel version: {{model}}\nOutput predictions with trend, magnitude, and reasoning.",
      variables: ["horizon", "threshold", "model"],
      tags: ["predictor", "vision-cortex"],
      governance: "MEDIUM"
    },
    {
      id: "AB_ARCHITECT_PROMPT",
      name: "Auto Builder Architect",
      domain: "auto_builder",
      level: "L5",
      description: "Build planning prompt for architect agent",
      template: "Create build plan for {{feature}}.\nConstraints: {{constraints}}\nGovernance: {{governance}}\nOutput: structured plan with steps, contracts, and validation criteria.",
      variables: ["feature", "constraints", "governance"],
      tags: ["architect", "auto-builder"],
      governance: "MEDIUM"
    },
    {
      id: "AB_GUARDIAN_PROMPT",
      name: "Auto Builder Guardian",
      domain: "auto_builder",
      level: "L7",
      description: "Compliance validation prompt for guardian agent",
      template: "Validate build artifacts against contracts.\nContracts: {{contracts}}\nGovernance level: {{governance}}\nMode: {{mode}}\nApprove, flag for review, or reject with reasoning.",
      variables: ["contracts", "governance", "mode"],
      tags: ["guardian", "auto-builder", "compliance"],
      governance: "HIGH"
    }
  ];
  
  if (domain) {
    return builtIn.filter(p => p.domain === domain);
  }
  
  return builtIn;
}

// Save a prompt template
export function savePrompt(template: PromptTemplate): void {
  ensureTemplatesDir();
  const filePath = path.join(TEMPLATES_DIR, `${template.id}.json`);
  fs.writeFileSync(filePath, JSON.stringify(template, null, 2));
  console.log(`📝 Prompt: Saved template ${template.id}`);
}

// Get a specific prompt by ID
export function getPrompt(promptId: string): PromptTemplate | null {
  const all = loadPrompts();
  return all.find(p => p.id === promptId) || null;
}

// Inject variables into a prompt template
export function injectPrompt(
  agent: string,
  context: PromptContext
): InjectedPrompt | null {
  // Find the best matching prompt for the agent
  const prompts = loadPrompts();
  
  // Look for agent-specific prompt first
  let template = prompts.find(p => 
    p.id.toLowerCase().includes(agent.toLowerCase()) ||
    p.tags.some(t => t.toLowerCase().includes(agent.toLowerCase()))
  );
  
  // Fall back to action-based matching
  if (!template && context.action) {
    template = prompts.find(p =>
      p.tags.some(t => t.toLowerCase().includes(context.action.toLowerCase()))
    );
  }
  
  // Fall back to default prompt
  if (!template) {
    template = prompts.find(p => p.id === "L1_MANUAL_ASSIST");
  }
  
  if (!template) {
    console.error(`❌ No prompt template found for agent ${agent}`);
    return null;
  }
  
  // Inject variables
  let content = template.template;
  const usedVariables: string[] = [];
  
  for (const varName of template.variables) {
    const placeholder = `{{${varName}}}`;
    if (content.includes(placeholder)) {
      const value = context.variables[varName] || `[${varName}]`;
      content = content.replace(new RegExp(placeholder, "g"), String(value));
      usedVariables.push(varName);
    }
  }
  
  // Add history context if available
  if (context.history && context.history.length > 0) {
    content += "\n\nRecent history:\n" + context.history.slice(-5).map(h => `- ${h}`).join("\n");
  }
  
  const injected: InjectedPrompt = {
    prompt_id: template.id,
    agent,
    content,
    injected_at: new Date().toISOString(),
    variables_used: usedVariables
  };
  
  console.log(`📝 Prompt: Injected ${template.id} for agent ${agent}`);
  return injected;
}

// List all available domains
export function listDomains(): string[] {
  const prompts = loadPrompts();
  const domains = new Set(prompts.map(p => p.domain));
  return Array.from(domains);
}

// Get prompts by governance level
export function getPromptsByGovernance(
  level: PromptTemplate["governance"]
): PromptTemplate[] {
  return loadPrompts().filter(p => p.governance === level);
}

// Initialize built-in templates (run once to create files)
export function initializeBuiltInPrompts(): void {
  ensureTemplatesDir();
  const builtIn = getBuiltInPrompts();
  
  for (const template of builtIn) {
    const filePath = path.join(TEMPLATES_DIR, `${template.id}.json`);
    if (!fs.existsSync(filePath)) {
      savePrompt(template);
    }
  }
  
  console.log(`📝 Prompt: Initialized ${builtIn.length} built-in templates`);
}

// Export for external use
export { TEMPLATES_DIR };
