from mcp.server import Server
import httpx
import os

ORCHESTRATOR_URL = os.getenv(
    "ORCHESTRATOR_URL",
    "https://orchestrator-896380409704.us-east1.run.app/execute"
)

server = Server("infinity-xos-mcp")

@server.tool()
async def execute(command: str, payload: dict | None = None):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            ORCHESTRATOR_URL,
            json={"command": command, "payload": payload or {}}
        )
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    server.run()
