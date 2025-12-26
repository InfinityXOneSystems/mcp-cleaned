/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vscode.cockpit
 * Validator: pending
 * 
 * Orchestrator Bridge for MCP
 * Function mcpInvoke(agent, action, payload) → POST to /mcp/execute.
 * Stream logs into the cockpit Webview.
 * Include exponential back-off retry and JSON error handling.
 */

import fetch from 'node-fetch';

const MCP_ENDPOINT = process.env.MCP_ENDPOINT || 'http://localhost:8000';
const MAX_RETRIES = 3;
const BASE_DELAY_MS = 500;

export interface MCPResponse {
  status: 'success' | 'error' | 'offline' | 'timeout';
  payload?: any;
  error?: string;
  duration_ms?: number;
  retries?: number;
}

export interface MCPPipelineStatus {
  status: string;
  pipeline: string;
  stage: string;
  agents?: string[];
  progress?: number;
  lastUpdate?: string;
}

export interface MCPAgentState {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  confidence?: number;
  lastRun?: string;
  duration_ms?: number;
}

// Exponential backoff delay
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Calculate backoff delay with jitter
function getBackoffDelay(attempt: number): number {
  const baseDelay = BASE_DELAY_MS * Math.pow(2, attempt);
  const jitter = Math.random() * 100;
  return baseDelay + jitter;
}

/**
 * Invoke an MCP agent with retry and error handling
 */
export async function mcpInvoke(
  agent: string,
  action: string,
  payload: any
): Promise<MCPResponse> {
  const start = Date.now();
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(`${MCP_ENDPOINT}/mcp/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-MCP-Agent': agent,
          'X-MCP-Action': action
        },
        body: JSON.stringify({ agent, action, payload }),
        timeout: 30000
      } as any);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      return {
        status: 'success',
        payload: data,
        duration_ms: Date.now() - start,
        retries: attempt
      };
    } catch (error) {
      lastError = error as Error;
      console.warn(`⚠️  MCP invoke attempt ${attempt + 1} failed:`, error);
      
      if (attempt < MAX_RETRIES - 1) {
        const backoff = getBackoffDelay(attempt);
        console.log(`   Retrying in ${backoff}ms...`);
        await delay(backoff);
      }
    }
  }
  
  // All retries exhausted
  return {
    status: 'offline',
    error: lastError?.message || 'Connection failed',
    duration_ms: Date.now() - start,
    retries: MAX_RETRIES
  };
}

/**
 * Get current pipeline status
 */
export async function mcpPipelineStatus(): Promise<MCPPipelineStatus> {
  try {
    const response = await fetch(`${MCP_ENDPOINT}/mcp/state`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      timeout: 5000
    } as any);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn('⚠️  Pipeline status unavailable:', error);
    return {
      status: 'offline',
      pipeline: 'unknown',
      stage: 'disconnected',
      lastUpdate: new Date().toISOString()
    };
  }
}

/**
 * Run a complete pipeline
 */
export async function mcpRunPipeline(payload: {
  pipeline: 'vision_cortex' | 'auto_builder';
  mode: 'DRY_RUN' | 'LIVE';
  context?: Record<string, any>;
}): Promise<MCPResponse> {
  const start = Date.now();
  
  try {
    const response = await fetch(`${MCP_ENDPOINT}/mcp/pipeline/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Pipeline': payload.pipeline
      },
      body: JSON.stringify(payload),
      timeout: 120000 // 2 minute timeout for pipelines
    } as any);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    return {
      status: 'success',
      payload: data,
      duration_ms: Date.now() - start
    };
  } catch (error) {
    return {
      status: 'error',
      error: (error as Error).message,
      duration_ms: Date.now() - start
    };
  }
}

/**
 * Get all agent states
 */
export async function mcpGetAgentStates(): Promise<MCPAgentState[]> {
  try {
    const response = await fetch(`${MCP_ENDPOINT}/mcp/agents`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      timeout: 5000
    } as any);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn('⚠️  Agent states unavailable:', error);
    return [];
  }
}

/**
 * Validate a result through MCP
 */
export async function mcpValidate(report: any): Promise<MCPResponse> {
  try {
    const response = await fetch(`${MCP_ENDPOINT}/mcp/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(report),
      timeout: 10000
    } as any);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return {
      status: 'success',
      payload: await response.json()
    };
  } catch (error) {
    return {
      status: 'offline',
      error: (error as Error).message
    };
  }
}

/**
 * Stream logs from an agent (for Webview integration)
 */
export async function mcpStreamLogs(
  agentId: string,
  onLog: (log: string) => void
): Promise<void> {
  try {
    const response = await fetch(`${MCP_ENDPOINT}/mcp/logs/${agentId}/stream`, {
      method: 'GET',
      headers: { 'Accept': 'text/event-stream' }
    });
    
    if (!response.ok || !response.body) {
      throw new Error('Stream not available');
    }
    
    const reader = response.body;
    const decoder = new TextDecoder();
    
    for await (const chunk of reader as any) {
      const text = decoder.decode(chunk);
      const lines = text.split('\n').filter(line => line.startsWith('data:'));
      
      for (const line of lines) {
        const data = line.replace('data:', '').trim();
        if (data) {
          onLog(data);
        }
      }
    }
  } catch (error) {
    console.warn(`⚠️  Log stream unavailable for ${agentId}:`, error);
    onLog(`[offline] Log stream unavailable`);
  }
}

/**
 * Health check for MCP gateway
 */
export async function mcpHealthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${MCP_ENDPOINT}/health`, {
      method: 'GET',
      timeout: 3000
    } as any);
    return response.ok;
  } catch {
    return false;
  }
}
