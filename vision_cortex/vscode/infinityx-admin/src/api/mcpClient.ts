import fetch from 'node-fetch';
export async function mcpInvoke(agent:string,action:string,payload:any){
  const r=await fetch('http://localhost:8000/mcp/execute',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({agent,action,payload})});
  return await r.json();
}

export async function mcpPipelineStatus() {
  return { status: 'ok', pipeline: 'mock', stage: 'idle' };
}

export async function mcpRunPipeline(payload: any) {
  return { status: 'ok', runId: 'mock-run', payload };
}

export interface MCPResponse {
  status: string;
  payload?: any;
}
