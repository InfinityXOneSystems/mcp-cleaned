/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: prompt.manager
 * Validator: pending
 */

export {
  loadPrompts,
  savePrompt,
  getPrompt,
  injectPrompt,
  listDomains,
  getPromptsByGovernance,
  initializeBuiltInPrompts,
  type PromptTemplate,
  type PromptContext,
  type InjectedPrompt
} from "./promptManager";
