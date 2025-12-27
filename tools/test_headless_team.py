import os
import sys
import json
import asyncio
import httpx

GATEWAY = os.environ.get('OMNI_GATEWAY_URL', 'http://localhost:8000')
OUT_FILE = os.environ.get('HEADLESS_TEST_OUT', 'tools/headless_test_results.json')

async def call_team():
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{GATEWAY}/api/agents/headless_team", timeout=10.0)
            team = r.json().get('team', [])
        except Exception as e:
            print(f"Failed to list team: {e}")
            return {"error": str(e)}

        results = []
        for t in team:
            name = t.get('name')
            # use example urls for test; prefer example.com
            url = 'https://example.com'
            payload = {"agent_name": name, "url": url}
            try:
                resp = await client.post(f"{GATEWAY}/api/agents/headless_team/execute", json=payload, timeout=30.0)
                results.append({"agent": name, "status": resp.status_code, "body": resp.json()})
            except Exception as e:
                results.append({"agent": name, "error": str(e)})

        out = {"gateway": GATEWAY, "results": results}
        with open(OUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2)
        return out

if __name__ == '__main__':
    res = asyncio.run(call_team())
    print(json.dumps(res, indent=2))
