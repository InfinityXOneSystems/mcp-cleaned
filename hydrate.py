import os
import httpx
import json
import sys
from datetime import datetime

# Config (can be overridden by env)
OWNER_NAME = os.environ.get('OWNER_NAME', 'Neo')
ORG_NAME = os.environ.get('ORG_NAME', 'Infinity X One Systems')
PRIMARY_REGION = os.environ.get('PRIMARY_REGION', 'us-east1')
TIMEZONE = os.environ.get('TIMEZONE', 'America/New_York')

MCP_AGENT_BASE = os.environ.get('MCP_AGENT_BASE', 'https://mcp-agent-896380409704.us-east1.run.app')
MEMORY_GATEWAY_BASE = os.environ.get('MEMORY_GATEWAY_BASE', 'https://memory-gateway-896380409704.us-east1.run.app')
ORCHESTRATOR_BASE = os.environ.get('ORCHESTRATOR_BASE', 'https://orchestrator-896380409704.us-east1.run.app')

SECRET_NAME = os.environ.get('GCP_SA_SECRET', 'projects/896380409704/secrets/workspace-sa-json')
MCP_API_KEY = os.environ.get('MCP_API_KEY')

HEADERS = {}
if MCP_API_KEY:
    HEADERS['Authorization'] = f'Bearer {MCP_API_KEY}'

client = httpx.Client(timeout=20.0)

def call(url, method='GET', json_body=None, allow_404=False):
    try:
        if method=='GET':
            r = client.get(url, headers=HEADERS)
        else:
            r = client.post(url, headers=HEADERS, json=json_body)
        if r.status_code==404 and allow_404:
            return None
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return r.text
    except Exception as e:
        return {'__error': str(e), 'status_code': getattr(e, 'response', None).status_code if getattr(e, 'response', None) is not None else None}

def load_service_account():
    url = f"{MCP_AGENT_BASE}/gcp/load_service_account"
    body = { 'secret_name': SECRET_NAME }
    print('-> Loading service account from Secret Manager via MCP...')
    res = call(url, method='POST', json_body=body)
    return res

def hydrate_memory():
    # try /recall then /memory/rehydrate
    url1 = f"{MEMORY_GATEWAY_BASE}/recall"
    url2 = f"{MEMORY_GATEWAY_BASE}/memory/rehydrate"
    print('-> Attempting memory recall from MEMORY_GATEWAY...')
    res = call(url1, method='POST', json_body={'owner': OWNER_NAME}, allow_404=True)
    if res is None:
        res = call(url2, method='POST', json_body={'namespace':'default','limit':20}, allow_404=True)
    return res

def discover_mcp():
    info = {}
    print('-> Checking MCP health and info...')
    info['health'] = call(f"{MCP_AGENT_BASE}/health", 'GET', allow_404=True)
    info['info'] = call(f"{MCP_AGENT_BASE}/info", 'GET', allow_404=True)
    # try tools endpoint
    info['tools'] = call(f"{MCP_AGENT_BASE}/tools", 'GET', allow_404=True)
    return info

def validate_orchestrator():
    print('-> Validating Orchestrator')
    o = {}
    o['health'] = call(f"{ORCHESTRATOR_BASE}/health", 'GET', allow_404=True)
    o['info'] = call(f"{ORCHESTRATOR_BASE}/info", 'GET', allow_404=True)
    # probe execute endpoint
    o['execute_probe'] = call(f"{ORCHESTRATOR_BASE}/execute", 'POST', json_body={'probe':True}, allow_404=True)
    return o

def main():
    summary = {'hydration_time': datetime.utcnow().isoformat() + 'Z'}
    print('\n===== INFINITY XOS HYDRATOR START =====')
    # STEP 1: load SA
    sa = load_service_account()
    summary['service_account'] = sa

    # STEP 2: hydrate memory
    mem = hydrate_memory()
    summary['memory'] = mem

    # STEP 3: discover MCP
    mcp = discover_mcp()
    summary['mcp'] = mcp

    # STEP 4: validate orchestrator
    orch = validate_orchestrator()
    summary['orchestrator'] = orch

    # Build Hydration Summary
    print('\n[Hydration Summary]')
    print(f"Owner: {OWNER_NAME}")
    if isinstance(mem, dict) and 'objectives' in mem:
        objs = mem.get('objectives')
        print(f"- Objectives: {len(objs) if objs else 0}")
    else:
        print(f"- Memory load: {('ok' if mem else 'none')}")
    print(f"- MCP health: {mcp.get('health')}")
    print(f"- Orchestrator health: {orch.get('health')}")

    # Executive answer: choose one high-leverage outcome
    print('\n[Executive Answer]')
    print('- Start targeted crawls on PlatinumFunding_SeedData (high priority seeds) and run rapid NLP urgency scoring')

    # Print 3 futures placeholder
    print('\n[3 Futures]')
    print('FUTURE A (Best): Rapid ingestion -> high urgency leads -> outreach pipeline seeded (7d)')
    print('FUTURE B (Base): Mixed signal; need tuning and dedupe (7-14d)')
    print('FUTURE C (Fail): Crawl noise, low precision; tune keywords and sources')

    # Decision table minimal
    print('\n[Decision Table]')
    print('Decision: Run Platinum seed crawls | Pros: immediate data | Cons: noise | Cost: compute | Time-to-impact: hours | Confidence: 70')

    # Actions to execute
    print('\n[Actions I will execute via MCP/Orchestrator]')
    print('- Enqueue crawl jobs for seeds (using /jobs/enqueue on MCP if available)')
    print('- Start crawler worker (local) and monitor results into memory namespace platinum_crawls')

    # Output the structured JSON summary into file
    out_path = os.path.join(os.getcwd(), 'hydrate_summary.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f'\nHydration summary written to {out_path}')
    print('===== HYDRATOR COMPLETE =====\n')

if __name__ == '__main__':
    main()
