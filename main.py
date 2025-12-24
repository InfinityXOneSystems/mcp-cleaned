import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

server = Server(
    name="mcp",
    version="1.0.0",
    capabilities={"tools": {}}
)

@server.tool(name="ping", description="Ping test")
async def ping():
    return [TextContent(type="text", text="pong")]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
